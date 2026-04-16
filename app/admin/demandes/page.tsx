"use client";
import React, { useEffect, useState } from 'react';
import { accountService } from '@/services/accounts';

interface AccountRequest {
    id: string;
    first_name: string;
    last_name: string;
    email: string;
    organisation: string;
    justification: string;
    status: string;
    created_at: string;
}

export default function DemandesComptes() {
    const [requests, setRequests] = useState<AccountRequest[]>([]);
    const [loading, setLoading] = useState(true);
    const [selectedRequest, setSelectedRequest] = useState<AccountRequest | null>(null);
    const [rejectReason, setRejectReason] = useState('');
    const [isRejectModalOpen, setIsRejectModalOpen] = useState(false);
    const [isApproveModalOpen, setIsApproveModalOpen] = useState(false);

    useEffect(() => {
        fetchRequests();
    }, []);

    const fetchRequests = async () => {
        try {
            setLoading(true);
            const data = await accountService.listRequests('PENDING');
            setRequests(data.items || []);
        } catch (error) {
            console.error('Error fetching requests:', error);
            alert('Erreur lors du chargement des demandes');
        } finally {
            setLoading(false);
        }
    };

    const handleApprove = async () => {
        if (!selectedRequest) return;
        try {
            await accountService.approveRequest(selectedRequest.id);
            alert(`Le compte de ${selectedRequest.first_name} a été approuvé`);
            setIsApproveModalOpen(false);
            setSelectedRequest(null);
            fetchRequests();
        } catch (error) {
            console.error('Error approving request:', error);
            alert('Erreur lors de l\'approbation');
        }
    };

    const handleReject = async () => {
        if (!selectedRequest || !rejectReason) return;
        try {
            await accountService.rejectRequest(selectedRequest.id, rejectReason);
            alert(`La demande de ${selectedRequest.first_name} a été rejetée`);
            setIsRejectModalOpen(false);
            setSelectedRequest(null);
            setRejectReason('');
            fetchRequests();
        } catch (error) {
            console.error('Error rejecting request:', error);
            alert('Erreur lors du rejet');
        }
    };

    return (
        <div className="page active" style={{ padding: '0 20px 40px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '32px' }}>
                <div>
                    <h1 style={{ fontSize: '24px', fontWeight: 700, color: 'var(--g1-text)', marginBottom: '4px', letterSpacing: '-0.5px' }}>Demandes de création de compte</h1>
                    <p style={{ color: 'var(--g1-muted)', fontSize: '14px' }}>Validez ou rejetez les demandes d'accès à la plateforme SIGMA Horizon.</p>
                </div>
            </div>

            <div className="pm-card">
                <div className="pm-hdr">
                    <svg viewBox="0 0 24 24" width="18" height="18" stroke="currentColor" fill="none" strokeWidth="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><polyline points="14 2 14 8 20 8" /><line x1="16" y1="13" x2="8" y2="13" /><line x1="16" y1="17" x2="8" y2="17" /><polyline points="10 9 9 9 8 9" /></svg>
                    Demandes en attente ({requests.length})
                </div>
                <div style={{ overflowX: 'auto' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
                        <thead style={{ background: 'rgba(255,255,255,0.02)' }}>
                            <tr>
                                <th style={{ padding: '16px 20px', textAlign: 'left', color: 'var(--g1-muted)', fontWeight: 600, borderBottom: '1px solid var(--g1-border)' }}>Utilisateur</th>
                                <th style={{ padding: '16px 20px', textAlign: 'left', color: 'var(--g1-muted)', fontWeight: 600, borderBottom: '1px solid var(--g1-border)' }}>Organisation</th>
                                <th style={{ padding: '16px 20px', textAlign: 'left', color: 'var(--g1-muted)', fontWeight: 600, borderBottom: '1px solid var(--g1-border)' }}>Date</th>
                                <th style={{ padding: '16px 20px', textAlign: 'right', color: 'var(--g1-muted)', fontWeight: 600, borderBottom: '1px solid var(--g1-border)' }}>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {loading ? (
                                <tr>
                                    <td colSpan={4} style={{ padding: '40px', textAlign: 'center', color: 'var(--g1-muted)' }}>Chargement des demandes...</td>
                                </tr>
                            ) : requests.length === 0 ? (
                                <tr>
                                    <td colSpan={4} style={{ padding: '40px', textAlign: 'center', color: 'var(--g1-muted)' }}>Aucune demande en attente.</td>
                                </tr>
                            ) : (
                                requests.map(req => (
                                    <tr key={req.id}>
                                        <td style={{ padding: '16px 20px', borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
                                            <div>
                                                <div style={{ fontWeight: 600, color: 'var(--g1-text)' }}>{req.first_name} {req.last_name}</div>
                                                <div style={{ fontSize: '12px', color: 'var(--g1-muted)' }}>{req.email}</div>
                                            </div>
                                        </td>
                                        <td style={{ padding: '16px 20px', borderBottom: '1px solid rgba(255,255,255,0.03)', color: 'var(--g1-text)' }}>
                                            {req.organisation}
                                        </td>
                                        <td style={{ padding: '16px 20px', borderBottom: '1px solid rgba(255,255,255,0.03)', color: 'var(--g1-muted)' }}>
                                            {new Date(req.created_at).toLocaleDateString('fr-FR')}
                                        </td>
                                        <td style={{ padding: '16px 20px', borderBottom: '1px solid rgba(255,255,255,0.03)', textAlign: 'right' }}>
                                            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
                                                <button
                                                    className="btn-ghost"
                                                    style={{ fontSize: '12px', padding: '6px 12px' }}
                                                    onClick={() => {
                                                        setSelectedRequest(req);
                                                        setIsApproveModalOpen(true);
                                                    }}
                                                >
                                                    Approuver
                                                </button>
                                                <button
                                                    className="btn-ghost"
                                                    style={{ fontSize: '12px', padding: '6px 12px', color: '#EF4444' }}
                                                    onClick={() => {
                                                        setSelectedRequest(req);
                                                        setIsRejectModalOpen(true);
                                                    }}
                                                >
                                                    Rejeter
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Approve Modal */}
            {isApproveModalOpen && selectedRequest && (
                <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, backgroundColor: 'rgba(15, 23, 42, 0.65)', backdropFilter: 'blur(4px)', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 1000, padding: '20px' }}>
                    <div style={{ background: '#0F1623', borderRadius: '16px', width: '100%', maxWidth: '500px', border: '1px solid var(--g1-border)', boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.3)' }}>
                        <div style={{ padding: '24px 32px 16px', borderBottom: '1px solid var(--g1-border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <h2 style={{ fontSize: '20px', fontWeight: 'bold', color: '#F8FAFC', margin: 0 }}>Approuver la demande</h2>
                            <button onClick={() => setIsApproveModalOpen(false)} style={{ background: 'none', border: 'none', color: '#64748B', cursor: 'pointer', padding: '4px' }}>
                                <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" strokeWidth="2" fill="none"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
                            </button>
                        </div>
                        <div style={{ padding: '24px 32px' }}>
                            <p style={{ color: 'var(--g1-text)', marginBottom: '16px' }}>
                                Voulez-vous approuver la demande de creation de compte pour <strong>{selectedRequest.first_name} {selectedRequest.last_name}</strong> ?
                            </p>
                            <div style={{ background: 'rgba(255,255,255,0.02)', padding: '16px', borderRadius: '8px', marginBottom: '24px' }}>
                                <div style={{ fontSize: '12px', color: 'var(--g1-muted)', marginBottom: '4px' }}>Justification fournie :</div>
                                <div style={{ color: 'var(--g1-text)', fontSize: '14px', fontStyle: 'italic' }}>"{selectedRequest.justification || 'Aucune justification fournie.'}"</div>
                            </div>
                            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
                                <button
                                    onClick={() => setIsApproveModalOpen(false)}
                                    style={{ padding: '10px 18px', background: 'transparent', border: '1px solid var(--g1-border)', color: '#F8FAFC', borderRadius: '8px', fontSize: '14px', fontWeight: 600, cursor: 'pointer' }}
                                >
                                    Annuler
                                </button>
                                <button
                                    onClick={handleApprove}
                                    style={{ padding: '10px 18px', background: '#2563EB', border: 'none', color: '#fff', borderRadius: '8px', fontSize: '14px', fontWeight: 600, cursor: 'pointer' }}
                                >
                                    Confirmer l'approbation
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Reject Modal */}
            {isRejectModalOpen && selectedRequest && (
                <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, backgroundColor: 'rgba(15, 23, 42, 0.65)', backdropFilter: 'blur(4px)', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 1000, padding: '20px' }}>
                    <div style={{ background: '#0F1623', borderRadius: '16px', width: '100%', maxWidth: '500px', border: '1px solid var(--g1-border)', boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.3)' }}>
                        <div style={{ padding: '24px 32px 16px', borderBottom: '1px solid var(--g1-border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <h2 style={{ fontSize: '20px', fontWeight: 'bold', color: '#F8FAFC', margin: 0 }}>Rejeter la demande</h2>
                            <button onClick={() => setIsRejectModalOpen(false)} style={{ background: 'none', border: 'none', color: '#64748B', cursor: 'pointer', padding: '4px' }}>
                                <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" strokeWidth="2" fill="none"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
                            </button>
                        </div>
                        <div style={{ padding: '24px 32px' }}>
                            <p style={{ color: 'var(--g1-text)', marginBottom: '20px' }}>
                                Veuillez indiquer la raison du rejet pour <strong>{selectedRequest.first_name} {selectedRequest.last_name}</strong>. Cet utilisateur recevra un e-mail avec cette explication.
                            </p>
                            <div style={{ marginBottom: '24px' }}>
                                <label style={{ display: 'block', fontSize: '14px', fontWeight: 600, color: '#F8FAFC', marginBottom: '8px' }}>Raison du rejet</label>
                                <textarea
                                    required
                                    placeholder="Ex: Justification insuffisante, Profil non conforme..."
                                    value={rejectReason}
                                    onChange={e => setRejectReason(e.target.value)}
                                    style={{ width: '100%', minHeight: '100px', padding: '12px 14px', background: 'rgba(255,255,255,0.03)', border: '1px solid var(--g1-border)', borderRadius: '8px', color: '#F8FAFC', fontSize: '14px', outline: 'none', resize: 'vertical' }}
                                />
                            </div>
                            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
                                <button
                                    onClick={() => setIsRejectModalOpen(false)}
                                    style={{ padding: '10px 18px', background: 'transparent', border: '1px solid var(--g1-border)', color: '#F8FAFC', borderRadius: '8px', fontSize: '14px', fontWeight: 600, cursor: 'pointer' }}
                                >
                                    Annuler
                                </button>
                                <button
                                    onClick={handleReject}
                                    disabled={!rejectReason}
                                    style={{ padding: '10px 18px', background: '#EF4444', border: 'none', color: '#fff', borderRadius: '8px', fontSize: '14px', fontWeight: 600, cursor: 'pointer', opacity: !rejectReason ? 0.5 : 1 }}
                                >
                                    Confirmer le rejet
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
