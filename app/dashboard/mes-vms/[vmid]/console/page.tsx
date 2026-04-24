"use client";

import React, { useEffect, useRef, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
// import RFB from '@novnc/novnc/lib/rfb'; // Removed static import
import { ArrowLeft, Monitor } from 'lucide-react';

export default function ConsoleViewer() {
    const params = useParams();
    const vmid = params.vmid as string;
    const router = useRouter();
    const containerRef = useRef<HTMLDivElement>(null);
    const rfbRef = useRef<any>(null);
    const [status, setStatus] = useState('Connecting...');
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        let rfb: any;
        let cancelled = false;

        const connect = async () => {
            if (!containerRef.current) return;

            try {
                setStatus('Fetching VNC ticket...');
                
                // Get the JWT token from localStorage
                const token = localStorage.getItem('horizon_token') || '';

                const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api/v1';
                const WS_BASE_URL = API_BASE_URL.replace('http', 'ws');

                // 1. Fetch the VNC ticket and port from the backend
                const resp = await fetch(`${API_BASE_URL}/vms/${vmid}/vnc-ticket`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`
                    }
                });

                if (!resp.ok) {
                    const errorText = await resp.text();
                    throw new Error(`Failed to get VNC ticket: ${resp.status} - ${errorText}`);
                }

                const json = await resp.json();
                const ticketData = json.data;
                const ticket = ticketData?.ticket || '';
                const port = ticketData?.port || '';

                if (!ticket || !port) {
                    throw new Error('No ticket or port received from server');
                }

                if (cancelled) return;

                // 2. Connect to our backend WebSocket proxy
                const encodedTicket = encodeURIComponent(ticket);
                const wsUrl = `${WS_BASE_URL}/vnc/${vmid}?port=${port}&ticket=${encodedTicket}`;
                console.log(`Connecting to VNC at: ${wsUrl}`);

                // Dynamic import noVNC
                const noVncModule: any = await import('@novnc/novnc/lib/rfb');
                
                // Handle different export formats (CJS vs ESM)
                let RFBConstructor;
                if (noVncModule.default) {
                    RFBConstructor = noVncModule.default.default || noVncModule.default;
                } else {
                    RFBConstructor = noVncModule;
                }

                if (typeof RFBConstructor !== 'function') {
                    throw new Error('RFB constructor not found in module');
                }

                // Configure noVNC
                rfb = new RFBConstructor(containerRef.current, wsUrl, {
                    credentials: { password: ticket },
                    wsProtocols: ['binary'],
                    shared: true,
                    view_only: false,
                    resizeSession: false
                });

                // Store reference for cleanup
                rfbRef.current = rfb;

                rfb.addEventListener('connect', () => {
                    console.log('VNC Connected successfully');
                    setStatus('Connected');
                    setError(null);

                    // After connection, try to set scaling
                    setTimeout(() => {
                        if (rfbRef.current) {
                            // Scale to fit container
                            rfbRef.current.scaleViewport = true;
                            rfbRef.current.clipViewport = false;

                            // Force a resize of the canvas
                            if (containerRef.current) {
                                const canvas = containerRef.current.querySelector('canvas');
                                if (canvas) {
                                    canvas.style.width = '100%';
                                    canvas.style.height = '100%';
                                    canvas.style.objectFit = 'contain';
                                }
                            }
                        }
                    }, 100);
                });

                rfb.addEventListener('disconnect', (e: any) => {
                    console.log('VNC Disconnected:', e.detail);
                    setStatus(e.detail.clean ? 'Disconnected' : 'Connection Failed');
                    if (!e.detail.clean) {
                        setError(`Disconnected: ${e.detail.reason || 'Unknown reason'}`);
                    }
                });

                rfb.addEventListener('securityfailure', (e: any) => {
                    console.error('Security failure:', e.detail);
                    setStatus('Authentication Failed');
                    setError(`Security failure: ${e.detail.reason}`);
                });

                rfb.addEventListener('desktopname', (e: any) => {
                    console.log('Desktop name:', e.detail.name);
                });

                // Set initial scaling options
                rfb.scaleViewport = true;
                rfb.clipViewport = false;
                rfb.qualityLevel = 6;
                rfb.compressionLevel = 2;

                console.log('RFB instance created and configured');

            } catch (error: any) {
                console.error("VNC connection error:", error);
                setStatus('Error connecting to VNC');
                setError(error.message);
            }
        };

        connect();

        return () => {
            cancelled = true;
            if (rfbRef.current) {
                try {
                    rfbRef.current.disconnect();
                } catch (e) {
                    console.error('Error disconnecting RFB:', e);
                }
            }
        };
    }, [vmid]);

    // Handle window resize to adjust canvas
    useEffect(() => {
        const handleResize = () => {
            if (rfbRef.current && containerRef.current) {
                const canvas = containerRef.current.querySelector('canvas');
                if (canvas) {
                    canvas.style.width = '100%';
                    canvas.style.height = '100%';
                    canvas.style.objectFit = 'contain';
                }
            }
        };

        window.addEventListener('resize', handleResize);
        return () => window.removeEventListener('resize', handleResize);
    }, []);

    return (
        <div className="min-h-screen bg-black text-gray-300 flex flex-col">
            <header className="bg-gray-900 border-b border-gray-800 p-4 flex justify-between items-center">
                <div className="flex items-center gap-4">
                    <button onClick={() => router.push(`/dashboard/mes-vms/${vmid}`)} className="p-2 hover:bg-gray-800 rounded transition text-gray-400 hover:text-white">
                        <ArrowLeft size={20} />
                    </button>
                    <h2 className="text-xl font-bold flex items-center gap-2 text-white">
                        <Monitor size={24} className="text-indigo-400" />
                        Console: VM {vmid}
                    </h2>
                </div>
                <div className="flex items-center gap-3">
                    <div className={`w-3 h-3 rounded-full ${status === 'Connected' ? 'bg-green-500 animate-pulse' :
                        status === 'Connecting...' ? 'bg-yellow-500' :
                            'bg-red-500'
                        }`}></div>
                    <span className="font-mono text-sm">{status}</span>
                </div>
            </header>

            {error && (
                <div className="bg-red-900/50 border-b border-red-800 p-3 text-red-200 text-sm">
                    <strong>Error:</strong> {error}
                </div>
            )}

            <div className="flex-1 flex bg-black items-center justify-center" style={{ minHeight: 0, position: 'relative' }}>
                <div
                    ref={containerRef}
                    style={{
                        width: '100%',
                        height: '100%',
                        display: 'flex',
                        position: 'relative',
                        alignItems: 'center',
                        justifyContent: 'center'
                    }}
                />
                {status !== 'Connected' && (
                    <div className="absolute inset-0 flex items-center justify-center bg-black/80">
                        <div className="text-center">
                            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-500 mx-auto mb-4"></div>
                            <p>{status}</p>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
