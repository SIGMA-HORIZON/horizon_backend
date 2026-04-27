"use client";
import React, { useEffect, useState } from 'react';
import { accountService } from '@/services/accounts';
import Modal, { ModalType } from '@/app/components/Modal';

interface User {
  id: string;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  role: string;
  organisation: string;
  is_active: boolean;
}

export default function Utilisateurs() {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [alertConfig, setAlertConfig] = useState<{ isOpen: boolean; type: ModalType; title: string; message: string }>({ isOpen: false, type: 'info', title: '', message: '' });

  const showAlert = (title: string, message: string, type: ModalType = 'info') => {
    setAlertConfig({ isOpen: true, title, message, type });
  };
  const closeAlert = () => {
    setAlertConfig(prev => ({ ...prev, isOpen: false }));
  };

  // States for new user form
  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    email: '',
    organisation: '',
    role: 'USER'
  });

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      setLoading(true);
      const data = await accountService.listUsers();
      setUsers(data.items || []);
    } catch (error) {
      console.error('Error fetching users:', error);
      showAlert('Erreur', 'Erreur lors du chargement des utilisateurs', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    // Implementation for direct user creation via API if needed
    // For now we just close the modal as the user requested "validation of requests"
    setIsModalOpen(false);
    showAlert('Information', 'Fonctionnalité de création directe en cours de développement. Utilisez les demandes de compte.', 'info');
  };

  const getInitials = (fn: string, ln: string) => {
    return ((fn[0] || '') + (ln[0] || '')).toUpperCase();
  };

  const getRoleBadgeClass = (role: string) => {
    if (role === 'ADMIN' || role === 'SUPER_ADMIN') return 'badge-blue';
    return '';
  };

  return (
    <div className="page active" style={{ padding: '0 20px 40px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '32px' }}>
        <div>
          <h1 style={{ fontSize: '24px', fontWeight: 700, color: 'var(--g1-text)', marginBottom: '4px', letterSpacing: '-0.5px' }}>Dossiers Utilisateurs</h1>
          <p style={{ color: 'var(--g1-muted)', fontSize: '14px' }}>Contrôle des privilèges d'accès, droits et supervision des quotas actifs.</p>
        </div>
        <button className="btn-accent" onClick={() => setIsModalOpen(true)} style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '10px 18px', fontSize: '14px' }}>
          <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" fill="none" strokeWidth="2.5"><circle cx="12" cy="12" r="10" /><line x1="12" y1="8" x2="12" y2="16" /><line x1="8" y1="12" x2="16" y2="12" /></svg>
          Créer un utilisateur
        </button>
      </div>

      <div className="pm-card">
        <div className="pm-hdr">
          <svg viewBox="0 0 24 24" width="18" height="18" stroke="currentColor" fill="none" strokeWidth="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" /><circle cx="9" cy="7" r="4" /><path d="M23 21v-2a4 4 0 0 0-3-3.87" /><path d="M16 3.13a4 4 0 0 1 0 7.75" /></svg>
          Répertoire principal
        </div>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
            <thead style={{ background: 'rgba(255,255,255,0.02)' }}>
              <tr>
                <th style={{ padding: '16px 20px', textAlign: 'left', color: 'var(--g1-muted)', fontWeight: 600, borderBottom: '1px solid var(--g1-border)' }}>Nom & E-mail</th>
                <th style={{ padding: '16px 20px', textAlign: 'left', color: 'var(--g1-muted)', fontWeight: 600, borderBottom: '1px solid var(--g1-border)' }}>Rôle</th>
                <th style={{ padding: '16px 20px', textAlign: 'left', color: 'var(--g1-muted)', fontWeight: 600, borderBottom: '1px solid var(--g1-border)' }}>Organisation</th>
                <th style={{ padding: '16px 20px', textAlign: 'left', color: 'var(--g1-muted)', fontWeight: 600, borderBottom: '1px solid var(--g1-border)' }}>Statut</th>
                <th style={{ padding: '16px 20px', textAlign: 'right', color: 'var(--g1-muted)', fontWeight: 600, borderBottom: '1px solid var(--g1-border)' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={5} style={{ padding: '40px', textAlign: 'center', color: 'var(--g1-muted)' }}>Chargement des utilisateurs...</td>
                </tr>
              ) : users.map(u => (
                <tr key={u.id}>
                  <td style={{ padding: '16px 20px', borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                      <div style={{ width: '32px', height: '32px', borderRadius: '50%', background: 'linear-gradient(135deg, var(--g1-accent), #3B82F6)', flexShrink: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontSize: '12px', fontWeight: 600 }}>
                        {getInitials(u.first_name, u.last_name)}
                      </div>
                      <div>
                        <div style={{ fontWeight: 600, color: 'var(--g1-text)' }}>{u.first_name} {u.last_name}</div>
                        <div style={{ fontSize: '12px', color: 'var(--g1-muted)' }}>{u.email}</div>
                      </div>
                    </div>
                  </td>
                  <td style={{ padding: '16px 20px', borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
                    <span className={`badge ${getRoleBadgeClass(u.role)}`}>
                      {u.role}
                    </span>
                  </td>
                  <td style={{ padding: '16px 20px', borderBottom: '1px solid rgba(255,255,255,0.03)', color: 'var(--g1-text)' }}>
                    {u.organisation}
                  </td>
                  <td style={{ padding: '16px 20px', borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
                    <span className={`badge ${u.is_active ? 'badge-on' : 'badge-off'}`}>
                      {u.is_active ? 'Actif' : 'Suspendu'}
                    </span>
                  </td>
                  <td style={{ padding: '16px 20px', borderBottom: '1px solid rgba(255,255,255,0.03)', textAlign: 'right' }}>
                    <button className="btn-ghost" style={{ fontSize: '12px', padding: '6px 12px' }}>Gérer</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal is kept but simplified for now */}
      {isModalOpen && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, backgroundColor: 'rgba(15, 23, 42, 0.65)', backdropFilter: 'blur(4px)', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 1000, padding: '20px' }}>
          <div style={{ background: '#0F1623', borderRadius: '16px', width: '100%', maxWidth: '450px', border: '1px solid var(--g1-border)', boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.3)' }}>
            <div style={{ padding: '24px 32px 16px', borderBottom: '1px solid var(--g1-border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h2 style={{ fontSize: '20px', fontWeight: 'bold', color: '#F8FAFC', margin: 0 }}>Créer un utilisateur</h2>
              <button onClick={() => setIsModalOpen(false)} style={{ background: 'none', border: 'none', color: '#64748B', cursor: 'pointer', padding: '4px' }}>
                <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" strokeWidth="2" fill="none"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
              </button>
            </div>
            <div style={{ padding: '24px 32px' }}>
              <p style={{ color: 'var(--g1-muted)', fontSize: '14px', marginBottom: '24px' }}>
                Pour créer un utilisateur, demandez-lui de soumettre une demande via la page d'inscription, puis validez-la dans l'onglet "Demandes de comptes".
              </p>
              <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                <button onClick={() => setIsModalOpen(false)} style={{ padding: '10px 18px', background: '#2563EB', border: 'none', color: '#fff', borderRadius: '8px', fontSize: '14px', fontWeight: 600, cursor: 'pointer' }}>Compris</button>
              </div>
            </div>
          </div>
        </div>
      )}
      <Modal {...alertConfig} onClose={closeAlert} />
    </div>
  );
}
