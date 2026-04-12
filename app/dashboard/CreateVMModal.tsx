"use client";
import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useVMs } from './VMContext';

interface CreateVMModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function CreateVMModal({ isOpen, onClose }: CreateVMModalProps) {
  const { addReservation } = useVMs();
  const router = useRouter();
  
  const [name, setName] = useState('');
  const [os, setOs] = useState('Ubuntu Server 22.04 LTS');
  const [cpu, setCpu] = useState(4);
  const [ram, setRam] = useState(8);
  const [storage, setStorage] = useState(100);

  if (!isOpen) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    addReservation({
      name: name || 'vm-projet-ornella',
      os: os.includes('Ubuntu') ? 'Ubuntu 22.04' : (os.includes('Debian') ? 'Debian 12' : 'Fedora 39'),
      cpu: cpu,
      ram: `${ram} Go`,
      storage: `${storage} Go`,
    });
    // Reset form
    setName('');
    setOs('Ubuntu Server 22.04 LTS');
    setCpu(4);
    setRam(8);
    setStorage(100);
    onClose();
    
    // Auto redirect to reservations tab so they can see their pending request
    router.push('/dashboard/reservations');
  };

  return (
    <div className="modal-overlay" style={overlayStyle}>
      <div className="modal-content" style={contentStyle}>
        <div style={headerStyle}>
          <div>
            <h2 style={titleStyle}>Nouvelle réservation VM</h2>
            <p style={subtitleStyle}>Votre demande sera soumise à validation par l'administrateur.</p>
          </div>
          <button onClick={onClose} style={closeBtnStyle}>
            <svg viewBox="0 0 24 24" width="24" height="24" stroke="currentColor" strokeWidth="2" fill="none" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
          </button>
        </div>

        <form onSubmit={handleSubmit} style={formStyle}>
          
          <div className="form-group" style={formGroupStyle}>
            <label style={labelStyle}>Nom de la VM</label>
            <input type="text" style={inputStyle} placeholder="vm-projet-ornella" value={name} onChange={e => setName(e.target.value)} />
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginTop: '32px', marginBottom: '20px' }}>
            <span style={stepNumStyle}>1</span> <span style={stepTextStyle}>Image OS</span>
            <div style={stepDividerStyle}></div>
          </div>

          <div className="form-group" style={formGroupStyle}>
            <select style={inputStyle} value={os} onChange={e => setOs(e.target.value)}>
              <option>Ubuntu Server 22.04 LTS</option>
              <option>Debian 12</option>
              <option>Fedora 39</option>
            </select>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginTop: '32px', marginBottom: '20px' }}>
            <span style={stepNumStyle}>2</span> <span style={stepTextStyle}>Ressources</span>
            <div style={stepDividerStyle}></div>
          </div>

          <div style={rowStyle}>
            <div className="form-group" style={{ ...formGroupStyle, flex: 1 }}>
              <label style={labelStyle}>vCPU</label>
              <input type="number" style={inputStyle} value={cpu} onChange={e => setCpu(Number(e.target.value))} />
            </div>
            <div className="form-group" style={{ ...formGroupStyle, flex: 1 }}>
              <label style={labelStyle}>RAM (Go)</label>
              <input type="number" style={inputStyle} value={ram} onChange={e => setRam(Number(e.target.value))} />
            </div>
            <div className="form-group" style={{ ...formGroupStyle, flex: 1 }}>
              <label style={labelStyle}>GPU</label>
              <input type="number" style={inputStyle} defaultValue="0" />
            </div>
          </div>

          <div className="form-group" style={formGroupStyle}>
            <label style={labelStyle}>Stockage (Go)</label>
            <input type="number" style={inputStyle} value={storage} onChange={e => setStorage(Number(e.target.value))} />
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginTop: '32px', marginBottom: '20px' }}>
            <span style={stepNumStyle}>3</span> <span style={stepTextStyle}>Durée</span>
            <div style={stepDividerStyle}></div>
          </div>

          <div className="form-group" style={formGroupStyle}>
            <label style={labelStyle}>Durée de la réservation (heures)</label>
            <input type="number" style={inputStyle} defaultValue="48" />
          </div>

          <div className="form-group" style={formGroupStyle}>
            <label style={labelStyle}>Justification / Projet</label>
            <textarea style={{ ...inputStyle, minHeight: '80px', resize: 'vertical' }} placeholder="Ex. : Entraînement modèle NLP pour le projet X..."></textarea>
          </div>

          <div style={footerStyle}>
            <button type="button" onClick={onClose} style={btnGhostStyle}>Annuler</button>
            <button type="submit" style={btnPrimaryStyle}>Soumettre la demande</button>
          </div>
        </form>
      </div>
    </div>
  );
}

// INLINE STYLES FOR THE MODAL
const overlayStyle: React.CSSProperties = {
  position: 'fixed',
  top: 0, left: 0, right: 0, bottom: 0,
  backgroundColor: 'rgba(15, 23, 42, 0.65)',
  backdropFilter: 'blur(4px)',
  display: 'flex',
  justifyContent: 'center',
  alignItems: 'center',
  zIndex: 1000,
  padding: '20px'
};

const contentStyle: React.CSSProperties = {
  background: '#ffffff',
  borderRadius: '16px',
  width: '100%',
  maxWidth: '560px',
  maxHeight: '90vh',
  overflowY: 'auto',
  boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
  position: 'relative'
};

const headerStyle: React.CSSProperties = {
  padding: '24px 32px 16px',
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'flex-start'
};

const titleStyle: React.CSSProperties = {
  fontSize: '22px',
  fontWeight: 'bold',
  color: '#0F172A',
  margin: '0 0 6px 0'
};

const subtitleStyle: React.CSSProperties = {
  fontSize: '14px',
  color: '#64748B',
  margin: 0
};

const closeBtnStyle: React.CSSProperties = {
  background: 'none',
  border: 'none',
  color: '#64748B',
  cursor: 'pointer',
  padding: '4px',
  marginTop: '-4px',
  marginRight: '-8px'
};

const stepContainerStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  padding: '0 32px 24px',
  borderBottom: '1px solid #E2E8F0',
  gap: '12px'
};

const stepStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: '8px'
};

const activeStepStyle: React.CSSProperties = {
  // Active style logic can go here if needed
};

const stepNumStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  width: '24px',
  height: '24px',
  borderRadius: '50%',
  border: '2px solid #94A3B8',
  color: '#64748B',
  fontSize: '12px',
  fontWeight: 'bold'
};

const stepNumActiveStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  width: '24px',
  height: '24px',
  borderRadius: '50%',
  border: '2px solid #2563EB',
  color: '#2563EB',
  fontSize: '12px',
  fontWeight: 'bold'
};

const stepTextStyle: React.CSSProperties = {
  fontSize: '14px',
  fontWeight: 600,
  color: '#64748B'
};

const stepDividerStyle: React.CSSProperties = {
  flex: 1,
  height: '1px',
  background: '#E2E8F0'
};

const formStyle: React.CSSProperties = {
  padding: '24px 32px'
};

const rowStyle: React.CSSProperties = {
  display: 'flex',
  gap: '16px'
};

const formGroupStyle: React.CSSProperties = {
  marginBottom: '20px',
  display: 'flex',
  flexDirection: 'column'
};

const labelStyle: React.CSSProperties = {
  fontSize: '14px',
  fontWeight: 600,
  color: '#1E293B',
  marginBottom: '8px'
};

const inputStyle: React.CSSProperties = {
  padding: '10px 14px',
  fontSize: '14px',
  color: '#0F172A',
  border: '1px solid #CBD5E1',
  borderRadius: '8px',
  outline: 'none',
  fontFamily: 'inherit',
  width: '100%',
  background: '#fff'
};

const footerStyle: React.CSSProperties = {
  display: 'flex',
  justifyContent: 'flex-end',
  gap: '12px',
  marginTop: '32px'
};

const btnGhostStyle: React.CSSProperties = {
  padding: '10px 18px',
  background: '#fff',
  border: '1px solid #CBD5E1',
  color: '#475569',
  borderRadius: '8px',
  fontSize: '14px',
  fontWeight: 600,
  cursor: 'pointer'
};

const btnPrimaryStyle: React.CSSProperties = {
  padding: '10px 18px',
  background: '#2563EB',
  border: 'none',
  color: '#fff',
  borderRadius: '8px',
  fontSize: '14px',
  fontWeight: 600,
  cursor: 'pointer'
};
