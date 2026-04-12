"use client";
import React, { useState } from 'react';

export default function Utilisateurs() {
  const [users, setUsers] = useState([
    { id: 1, init: 'OM', color: 'linear-gradient(135deg, var(--g1-accent), #3B82F6)', name: "Ornella Mbo'o", email: "ornella.mboo@enspy.cm", role: "Utilisateur", roleClass: "", org: "Étudiante — M2 INFO", quotaUsed: 3, quotaMax: 5, fillProps: { width: '60%' } },
    { id: 2, init: 'JD', color: 'linear-gradient(135deg, #10B981, #059669)', name: "Jean Dupont", email: "jean.dupont@enspy.cm", role: "Admin", roleClass: "badge-blue", org: "Département Mécanique", quotaUsed: 1, quotaMax: 2, fillProps: { width: '50%', background: 'var(--g1-warn)' } }
  ]);

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [newName, setNewName] = useState('');
  const [newEmail, setNewEmail] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [newRole, setNewRole] = useState('Utilisateur');

  const handleCreateUser = (e: React.FormEvent) => {
    e.preventDefault();

    const roleClass = newRole === 'Admin' ? 'badge-blue' : '';
    const initials = newName.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase() || 'U';

    const newUser = {
      id: Date.now(),
      init: initials,
      color: 'linear-gradient(135deg, #8B5CF6, #6D28D9)',
      name: newName || 'Nouvel Utilisateur',
      email: newEmail || 'email@enspy.cm',
      role: newRole,
      roleClass: roleClass,
      org: "Nouvel Utilisateur",
      quotaUsed: 0,
      quotaMax: 2,
      fillProps: { width: '0%' }
    };

    setUsers([...users, newUser]);
    setIsModalOpen(false);
    
    // Reset form
    setNewName('');
    setNewEmail('');
    setNewPassword('');
    setNewRole('Utilisateur');
  };

  return (
    <div className="page active" style={{ padding: '0 20px 40px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '32px' }}>
        <div>
          <h1 style={{ fontSize: '24px', fontWeight: 700, color: 'var(--g1-text)', marginBottom: '4px', letterSpacing: '-0.5px' }}>Dossiers Utilisateurs</h1>
          <p style={{ color: 'var(--g1-muted)', fontSize: '14px' }}>Contrôle des privilèges d'accès, droits et supervision des quotas actifs.</p>
        </div>
        <button className="btn-accent" onClick={() => setIsModalOpen(true)} style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '10px 18px', fontSize: '14px' }}>
          <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" fill="none" strokeWidth="2.5"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="16"/><line x1="8" y1="12" x2="16" y2="12"/></svg>
          Créer un utilisateur
        </button>
      </div>

      <div className="pm-card">
        <div className="pm-hdr">
          <svg viewBox="0 0 24 24"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
          Répertoire principal
        </div>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
            <thead style={{ background: 'rgba(255,255,255,0.02)' }}>
              <tr>
                <th style={{ padding: '16px 20px', textAlign: 'left', color: 'var(--g1-muted)', fontWeight: 600, borderBottom: '1px solid var(--g1-border)' }}>Nom & E-mail</th>
                <th style={{ padding: '16px 20px', textAlign: 'left', color: 'var(--g1-muted)', fontWeight: 600, borderBottom: '1px solid var(--g1-border)' }}>Rôle</th>
                <th style={{ padding: '16px 20px', textAlign: 'left', color: 'var(--g1-muted)', fontWeight: 600, borderBottom: '1px solid var(--g1-border)' }}>Organisation</th>
                <th style={{ padding: '16px 20px', textAlign: 'left', color: 'var(--g1-muted)', fontWeight: 600, borderBottom: '1px solid var(--g1-border)' }}>VMs Autorisées</th>
                <th style={{ padding: '16px 20px', textAlign: 'left', color: 'var(--g1-muted)', fontWeight: 600, borderBottom: '1px solid var(--g1-border)' }}>Statut du compte</th>
                <th style={{ padding: '16px 20px', textAlign: 'right', color: 'var(--g1-muted)', fontWeight: 600, borderBottom: '1px solid var(--g1-border)' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.map(u => (
                <tr key={u.id}>
                  <td style={{ padding: '16px 20px', borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                      <div style={{ width: '32px', height: '32px', borderRadius: '50%', background: u.color, flexShrink: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontSize: '12px', fontWeight: 600 }}>{u.init}</div>
                      <div>
                        <div style={{ fontWeight: 600, color: 'var(--g1-text)' }}>{u.name}</div>
                        <div style={{ fontSize: '12px', color: 'var(--g1-muted)' }}>{u.email}</div>
                      </div>
                    </div>
                  </td>
                  <td style={{ padding: '16px 20px', borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
                    <span className={`badge ${u.roleClass}`} style={!u.roleClass ? { background: 'rgba(255,255,255,0.05)', border: '1px solid var(--g1-border)', color: 'var(--g1-text)' } : {}}>
                      {u.role}
                    </span>
                  </td>
                  <td style={{ padding: '16px 20px', borderBottom: '1px solid rgba(255,255,255,0.03)', color: 'var(--g1-text)' }}>
                    {u.org}
                  </td>
                  <td style={{ padding: '16px 20px', borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{ width: '30px' }}>{u.quotaUsed}/{u.quotaMax}</span>
                      <div className="mini-bar"><div className="mini-fill" style={u.fillProps}></div></div>
                    </div>
                  </td>
                  <td style={{ padding: '16px 20px', borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
                    <span className="badge badge-on">Actif</span>
                  </td>
                  <td style={{ padding: '16px 20px', borderBottom: '1px solid rgba(255,255,255,0.03)', textAlign: 'right' }}>
                    <button className="btn-ghost" style={{ fontSize: '12px', padding: '6px 12px' }}>Gérer le quota</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal d'ajout d'utilisateur */}
      {isModalOpen && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, backgroundColor: 'rgba(15, 23, 42, 0.65)', backdropFilter: 'blur(4px)', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 1000, padding: '20px' }}>
          <div style={{ background: '#0F1623', borderRadius: '16px', width: '100%', maxWidth: '450px', border: '1px solid var(--g1-border)', boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.3)' }}>
            <div style={{ padding: '24px 32px 16px', borderBottom: '1px solid var(--g1-border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h2 style={{ fontSize: '20px', fontWeight: 'bold', color: '#F8FAFC', margin: 0 }}>Créer un utilisateur</h2>
              <button onClick={() => setIsModalOpen(false)} style={{ background: 'none', border: 'none', color: '#64748B', cursor: 'pointer', padding: '4px' }}>
                <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" strokeWidth="2" fill="none"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
              </button>
            </div>
            <form onSubmit={handleCreateUser} style={{ padding: '24px 32px' }}>
              
              <div style={{ marginBottom: '20px' }}>
                <label style={{ display: 'block', fontSize: '14px', fontWeight: 600, color: '#F8FAFC', marginBottom: '8px' }}>Nom complet</label>
                <input required type="text" placeholder="Ex: Jean Dupont" value={newName} onChange={e => setNewName(e.target.value)} style={{ width: '100%', padding: '10px 14px', background: 'rgba(255,255,255,0.03)', border: '1px solid var(--g1-border)', borderRadius: '8px', color: '#F8FAFC', fontSize: '14px', outline: 'none' }} />
              </div>

              <div style={{ marginBottom: '20px' }}>
                <label style={{ display: 'block', fontSize: '14px', fontWeight: 600, color: '#F8FAFC', marginBottom: '8px' }}>Adresse E-mail</label>
                <input required type="email" placeholder="email@enspy.cm" value={newEmail} onChange={e => setNewEmail(e.target.value)} style={{ width: '100%', padding: '10px 14px', background: 'rgba(255,255,255,0.03)', border: '1px solid var(--g1-border)', borderRadius: '8px', color: '#F8FAFC', fontSize: '14px', outline: 'none' }} />
              </div>

              <div style={{ marginBottom: '20px' }}>
                <label style={{ display: 'block', fontSize: '14px', fontWeight: 600, color: '#F8FAFC', marginBottom: '8px' }}>Mot de passe initial</label>
                <input required type="password" placeholder="••••••••" value={newPassword} onChange={e => setNewPassword(e.target.value)} style={{ width: '100%', padding: '10px 14px', background: 'rgba(255,255,255,0.03)', border: '1px solid var(--g1-border)', borderRadius: '8px', color: '#F8FAFC', fontSize: '14px', outline: 'none' }} />
              </div>

              <div style={{ marginBottom: '32px' }}>
                <label style={{ display: 'block', fontSize: '14px', fontWeight: 600, color: '#F8FAFC', marginBottom: '8px' }}>Rôle d'accès</label>
                <select value={newRole} onChange={e => setNewRole(e.target.value)} style={{ width: '100%', padding: '10px 14px', background: '#1E293B', border: '1px solid var(--g1-border)', borderRadius: '8px', color: '#F8FAFC', fontSize: '14px', outline: 'none' }}>
                  <option value="Utilisateur">Utilisateur</option>
                  <option value="Admin">Admin</option>
                </select>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
                <button type="button" onClick={() => setIsModalOpen(false)} style={{ padding: '10px 18px', background: 'transparent', border: '1px solid var(--g1-border)', color: '#F8FAFC', borderRadius: '8px', fontSize: '14px', fontWeight: 600, cursor: 'pointer' }}>Annuler</button>
                <button type="submit" style={{ padding: '10px 18px', background: '#2563EB', border: 'none', color: '#fff', borderRadius: '8px', fontSize: '14px', fontWeight: 600, cursor: 'pointer' }}>Créer l'utilisateur</button>
              </div>

            </form>
          </div>
        </div>
      )}

    </div>
  )
}
