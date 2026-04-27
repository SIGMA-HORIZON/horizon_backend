"use client";
import React from 'react';
import { AlertCircle, CheckCircle2, Info, XCircle } from 'lucide-react';

export type ModalType = 'info' | 'success' | 'error' | 'confirm';

interface ModalProps {
    isOpen: boolean;
    type: ModalType;
    title: string;
    message: string;
    onClose?: () => void;
    onConfirm?: () => void;
    confirmText?: string;
    cancelText?: string;
}

export default function Modal({
    isOpen,
    type,
    title,
    message,
    onClose,
    onConfirm,
    confirmText = "Confirmer",
    cancelText = "Annuler"
}: ModalProps) {
    if (!isOpen) return null;

    const getStyles = () => {
        switch (type) {
            case 'success':
                return { icon: <CheckCircle2 className="text-green-500 w-6 h-6" />, btn: 'bg-green-600 hover:bg-green-700' };
            case 'error':
                return { icon: <XCircle className="text-red-500 w-6 h-6" />, btn: 'bg-red-600 hover:bg-red-700' };
            case 'confirm':
                return { icon: <AlertCircle className="text-orange-500 w-6 h-6" />, btn: 'bg-orange-600 hover:bg-orange-700' };
            case 'info':
            default:
                return { icon: <Info className="text-blue-500 w-6 h-6" />, btn: 'bg-blue-600 hover:bg-blue-700' };
        }
    };

    const styles = getStyles();

    return (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, backgroundColor: 'rgba(15, 23, 42, 0.65)', backdropFilter: 'blur(4px)', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 9999, padding: '20px' }}>
            <div style={{ background: '#0F1623', borderRadius: '16px', width: '100%', maxWidth: '450px', border: '1px solid var(--g1-border)', boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.3)' }}>
                <div style={{ padding: '24px 32px 16px', borderBottom: '1px solid var(--g1-border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                        {styles.icon}
                        <h2 style={{ fontSize: '20px', fontWeight: 'bold', color: '#F8FAFC', margin: 0 }}>{title}</h2>
                    </div>
                    {onClose && (
                        <button onClick={onClose} style={{ background: 'none', border: 'none', color: '#64748B', cursor: 'pointer', padding: '4px' }}>
                            <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" strokeWidth="2" fill="none"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
                        </button>
                    )}
                </div>
                <div style={{ padding: '24px 32px' }}>
                    <p style={{ color: 'var(--g1-text)', fontSize: '15px', lineHeight: '1.5', margin: '0 0 24px 0' }}>{message}</p>
                    <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
                        {type === 'confirm' && onClose && (
                            <button
                                onClick={onClose}
                                style={{ padding: '10px 18px', background: 'transparent', border: '1px solid var(--g1-border)', color: '#F8FAFC', borderRadius: '8px', fontSize: '14px', fontWeight: 600, cursor: 'pointer', transition: 'all 0.2s' }}
                            >
                                {cancelText}
                            </button>
                        )}
                        <button
                            onClick={onConfirm || onClose}
                            className={`transition-colors text-white rounded-lg px-5 py-2.5 text-sm font-semibold cursor-pointer ${styles.btn}`}
                        >
                            {type === 'confirm' ? confirmText : 'OK'}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
