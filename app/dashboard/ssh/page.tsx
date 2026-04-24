"use client";
import React, { useState } from 'react';

export default function SshKeys() {
  const [isModalOpen, setIsModalOpen] = useState(false);

  return (
    <div className="page active" id="pg-ssh" style={{ padding: '0 20px 40px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '32px' }}>
        <div>
          <h1 style={{ fontSize: '28px', fontWeight: 700, color: 'var(--g1-text)', marginBottom: '8px', letterSpacing: '-0.5px' }}>Clés SSH</h1>
          <p style={{ color: 'var(--g1-muted)', fontSize: '15px' }}>Gérez les clés de sécurité injectées automatiquement dans vos VMs de calcul.</p>
        </div>
        <button className="btn-accent" onClick={() => setIsModalOpen(true)} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <svg viewBox="0 0 24 24" width="18" height="18" stroke="currentColor" fill="none" strokeWidth="2.5"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
          Ajouter une clé SSH
        </button>
      </div>

      <div className="pm-card">
        <div className="pm-hdr">
          <svg viewBox="0 0 24 24"><rect x="2" y="4" width="20" height="16" rx="2"/><path d="M8 12l2 2 4-4"/></svg>
          Clés SSH enregistrées
        </div>
        
        <div className="pm-body" style={{ padding: 0 }}>
          {/* Item 1 */}
          <div style={{ padding: '24px', borderBottom: '1px solid var(--g1-border)', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div style={{ display: 'flex', gap: '16px' }}>
              <div style={{ width: '40px', height: '40px', borderRadius: '8px', background: 'rgba(0,180,216,0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, border: '1px solid rgba(0,180,216,0.3)' }}>
                <svg viewBox="0 0 24 24" width="20" height="20" stroke="var(--g1-accent)" fill="none" strokeWidth="2.5"><rect x="2" y="4" width="20" height="16" rx="2"/><path d="M8 12l2 2 4-4"/></svg>
              </div>
              <div>
                <h4 style={{ fontSize: '16px', fontWeight: '600', color: 'var(--g1-text)', marginBottom: '6px' }}>MacBook Pro Ornella</h4>
                <p style={{ fontSize: '13px', fontFamily: 'monospace', color: 'var(--g1-muted)', marginBottom: '10px', background: 'rgba(255,255,255,0.03)', border: '1px solid var(--g1-border)', padding: '6px 10px', borderRadius: '6px' }}>SHA256:xK2mP4rQn8vL1oZ3jT6wY9bA5sC7dE0fG · ed25519</p>
                <div style={{ fontSize: '12px', color: 'var(--g1-off)', display: 'flex', alignItems: 'center', gap: '6px', fontWeight: 500 }}>
                  <svg viewBox="0 0 24 24" width="12" height="12" stroke="currentColor" fill="none"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
                  Ajoutée le 21/03/2026
                </div>
              </div>
            </div>
            <div style={{ display: 'flex', gap: '8px' }}>
              <button className="btn-ghost" style={{ fontSize: '13px', padding: '6px 12px' }}>Copier</button>
              <button className="btn-ghost" style={{ fontSize: '13px', padding: '6px 12px', borderColor: 'rgba(239,68,68,0.3)', color: 'var(--g1-err)' }}>Supprimer</button>
            </div>
          </div>

          {/* Item 2 */}
          <div style={{ padding: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div style={{ display: 'flex', gap: '16px' }}>
              <div style={{ width: '40px', height: '40px', borderRadius: '8px', background: 'rgba(37,99,235,0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, border: '1px solid rgba(37,99,235,0.3)' }}>
                <svg viewBox="0 0 24 24" width="20" height="20" stroke="var(--g1-accent2)" fill="none" strokeWidth="2.5"><rect x="2" y="4" width="20" height="16" rx="2"/><path d="M8 12l2 2 4-4"/></svg>
              </div>
              <div>
                <h4 style={{ fontSize: '16px', fontWeight: '600', color: 'var(--g1-text)', marginBottom: '6px' }}>Laptop Linux Ornella</h4>
                <p style={{ fontSize: '13px', fontFamily: 'monospace', color: 'var(--g1-muted)', marginBottom: '10px', background: 'rgba(255,255,255,0.03)', border: '1px solid var(--g1-border)', padding: '6px 10px', borderRadius: '6px' }}>SHA256:aB3nM7kP2qV5uX9wR1tJ4hL6yN8cZ0eF · ed25519</p>
                <div style={{ fontSize: '12px', color: 'var(--g1-off)', display: 'flex', alignItems: 'center', gap: '6px', fontWeight: 500 }}>
                  <svg viewBox="0 0 24 24" width="12" height="12" stroke="currentColor" fill="none"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
                  Ajoutée le 25/03/2026
                </div>
              </div>
            </div>
            <div style={{ display: 'flex', gap: '8px' }}>
              <button className="btn-ghost" style={{ fontSize: '13px', padding: '6px 12px' }}>Copier</button>
              <button className="btn-ghost" style={{ fontSize: '13px', padding: '6px 12px', borderColor: 'rgba(239,68,68,0.3)', color: 'var(--g1-err)' }}>Supprimer</button>
            </div>
          </div>
        </div>
      </div>

      {isModalOpen && (
        <div style={overlayStyle}>
          <div style={contentStyle}>
            <div style={headerStyle}>
              <div>
                <h2 style={titleStyle}>Ajouter une clé SSH</h2>
                <p style={subtitleStyle}>Collez votre clé publique (~/.ssh/id_ed25519.pub)</p>
              </div>
              <button onClick={() => setIsModalOpen(false)} style={closeBtnStyle}>
                <svg viewBox="0 0 24 24" width="24" height="24" stroke="currentColor" strokeWidth="2" fill="none" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
              </button>
            </div>

            <form onSubmit={(e) => { e.preventDefault(); setIsModalOpen(false); }} style={formStyle}>
              <div style={formGroupStyle}>
                <label style={labelStyle}>Nom de la clé</label>
                <input type="text" style={inputStyle} placeholder="Ex. : MacBook Ornella" required />
              </div>

              <div style={formGroupStyle}>
                <label style={labelStyle}>Clé publique</label>
                <textarea 
                  style={{ ...inputStyle, minHeight: '120px', resize: 'vertical', fontFamily: 'monospace', fontSize: '13px' }} 
                  placeholder="ssh-ed25519 AAAA..."
                  required
                ></textarea>
              </div>

              <div style={footerStyle}>
                <button type="button" onClick={() => setIsModalOpen(false)} style={btnGhostStyle}>Annuler</button>
                <button type="submit" style={btnPrimaryStyle}>Enregistrer</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

const overlayStyle: React.CSSProperties = {
  position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
  backgroundColor: 'rgba(3, 6, 16, 0.85)', backdropFilter: 'blur(8px)',
  display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 1000, padding: '20px'
};

const contentStyle: React.CSSProperties = {
  background: 'var(--g1-card)', border: '1px solid var(--g1-border)', borderTop: '1px solid rgba(0,180,216,0.4)', borderRadius: '16px',
  width: '100%', maxWidth: '500px', boxShadow: '0 20px 40px rgba(0,0,0,0.6)', position: 'relative'
};

const headerStyle: React.CSSProperties = {
  padding: '24px 32px 16px', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', borderBottom: '1px solid var(--g1-border)'
};

const titleStyle: React.CSSProperties = { fontSize: '20px', fontWeight: 'bold', color: 'var(--g1-text)', margin: '0 0 6px 0' };
const subtitleStyle: React.CSSProperties = { fontSize: '14px', color: 'var(--g1-muted)', margin: 0 };
const closeBtnStyle: React.CSSProperties = { background: 'none', border: 'none', color: 'var(--g1-muted)', cursor: 'pointer', padding: '4px', marginTop: '-4px', marginRight: '-8px' };
const formStyle: React.CSSProperties = { padding: '24px 32px' };
const formGroupStyle: React.CSSProperties = { marginBottom: '20px', display: 'flex', flexDirection: 'column' };
const labelStyle: React.CSSProperties = { fontSize: '12px', fontWeight: 600, color: 'var(--g1-muted)', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.8px' };
const inputStyle: React.CSSProperties = {
  padding: '12px 14px', fontSize: '14px', color: 'var(--g1-text)',
  border: '1px solid var(--g1-border)', borderRadius: '8px', outline: 'none', fontFamily: 'inherit', width: '100%',
  background: 'rgba(255,255,255,0.03)', marginTop: '8px',
  transition: 'border-color 0.2s',
};
const footerStyle: React.CSSProperties = { display: 'flex', justifyContent: 'flex-end', gap: '12px', marginTop: '32px' };

const btnGhostStyle: React.CSSProperties = { padding: '10px 18px', background: 'transparent', border: '1px solid var(--g1-border)', color: 'var(--g1-text)', borderRadius: '8px', fontSize: '14px', fontWeight: 500, cursor: 'pointer', transition: 'all 0.2s' };
const btnPrimaryStyle: React.CSSProperties = { padding: '10px 18px', background: 'var(--g1-accent2)', border: 'none', color: '#fff', borderRadius: '8px', fontSize: '14px', fontWeight: 600, cursor: 'pointer', transition: 'all 0.2s' };
