"use client";
import React, { useState, useEffect } from 'react';
import { adminService } from '../../../services/admin';
import IsoUploadModal from './IsoUploadModal';
import Modal, { ModalType } from '@/app/components/Modal';

export default function OSBibliotheque() {
  const [activeTab, setActiveTab] = useState('templates'); // 'templates' | 'isos'
  const [loading, setLoading] = useState(true);
  const [templates, setTemplates] = useState<any[]>([]);
  const [isos, setIsos] = useState<any[]>([]);

  // Modals
  const [isIsoModalOpen, setIsIsoModalOpen] = useState(false);
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const [alertConfig, setAlertConfig] = useState<{ isOpen: boolean; type: ModalType; title: string; message: string }>({ isOpen: false, type: 'info', title: '', message: '' });

  const showAlert = (title: string, message: string, type: ModalType = 'info') => {
    setAlertConfig({ isOpen: true, title, message, type });
  };
  const closeAlert = () => {
    setAlertConfig(prev => ({ ...prev, isOpen: false }));
  };

  // Add ISO to DB form state
  const [newName, setNewName] = useState('');
  const [newFilename, setNewFilename] = useState('');
  const [osFamily, setOsFamily] = useState('Linux');
  const [osVersion, setOsVersion] = useState('');
  const [newDesc, setNewDesc] = useState('');

  const fetchData = async () => {
    setLoading(true);
    try {
      const tData = await adminService.listIsoTemplates();
      const iData = await adminService.listIsos();
      setTemplates(tData.items || []);
      setIsos(iData.items || []);
    } catch (err) {
      console.error("Erreur lors du chargement de la bibliothèque:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, []);

  const handleAddIso = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await adminService.createIso({
        name: newName,
        filename: newFilename,
        os_family: osFamily,
        os_version: osVersion,
        description: newDesc
      });
      setIsIsoModalOpen(false);
      fetchData();
      setNewName(''); setNewFilename(''); setOsVersion(''); setNewDesc('');
    } catch (err) {
      showAlert('Erreur', "Erreur lors de l'ajout de l'ISO", 'error');
    }
  };

  return (
    <div className="page active" style={{ padding: '0 20px 40px' }}>
      {/* Page Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '32px', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <h1 style={{ fontSize: '24px', fontWeight: 700, color: 'var(--g1-text)', marginBottom: '4px', letterSpacing: '-0.5px' }}>
            Bibliothèque &amp; ISO
          </h1>
          <p style={{ color: 'var(--g1-muted)', fontSize: '14px' }}>
            Gérez les images templates et téléchargez des fichiers ISO pour vos installations personnalisées.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '10px', alignItems: 'center', flexWrap: 'wrap' }}>
          {/* Tab switcher */}
          <div style={{ display: 'flex', background: 'rgba(255,255,255,0.05)', padding: '4px', borderRadius: '10px' }}>
            <button
              onClick={() => setActiveTab('templates')}
              style={{ padding: '8px 16px', border: 'none', background: activeTab === 'templates' ? 'rgba(255,255,255,0.1)' : 'transparent', color: activeTab === 'templates' ? 'white' : 'var(--g1-muted)', borderRadius: '8px', fontSize: '13px', fontWeight: 600, cursor: 'pointer', transition: 'all 0.2s' }}
            >Templates</button>
            <button
              onClick={() => setActiveTab('isos')}
              style={{ padding: '8px 16px', border: 'none', background: activeTab === 'isos' ? 'rgba(255,255,255,0.1)' : 'transparent', color: activeTab === 'isos' ? 'white' : 'var(--g1-muted)', borderRadius: '8px', fontSize: '13px', fontWeight: 600, cursor: 'pointer', transition: 'all 0.2s' }}
            >Fichiers ISO</button>
          </div>

          {/* Action buttons for ISO tab */}
          {activeTab === 'isos' && (
            <>
              {/* Proxmox Upload button — highlighted */}
              <button
                id="btn-upload-proxmox-iso"
                onClick={() => setIsUploadModalOpen(true)}
                style={{
                  display: 'flex', alignItems: 'center', gap: '8px',
                  padding: '9px 18px',
                  background: 'linear-gradient(135deg, #6366f1, #4f46e5)',
                  border: 'none', color: 'white',
                  borderRadius: '10px', fontSize: '13px', fontWeight: 600,
                  cursor: 'pointer',
                  boxShadow: '0 4px 14px rgba(99,102,241,0.35)',
                  transition: 'all 0.2s',
                }}
              >
                <svg viewBox="0 0 24 24" width="15" height="15" stroke="currentColor" fill="none" strokeWidth="2.5">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                  <polyline points="17 8 12 3 7 8" />
                  <line x1="12" y1="3" x2="12" y2="15" />
                </svg>
                Uploader sur Proxmox
              </button>

              {/* Register existing ISO button */}
              <button
                id="btn-register-iso"
                className="btn-accent"
                onClick={() => setIsIsoModalOpen(true)}
                style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
              >
                <svg viewBox="0 0 24 24" width="15" height="15" stroke="currentColor" fill="none" strokeWidth="2.5">
                  <line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" />
                </svg>
                Référencer ISO
              </button>
            </>
          )}
        </div>
      </div>

      {/* ── TEMPLATES TAB ── */}
      {activeTab === 'templates' && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '24px' }}>
          {templates.map(t => (
            <div key={t.id} className="pm-card" style={{ padding: '24px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
                <div style={{ width: '48px', height: '48px', borderRadius: '12px', background: 'rgba(255,255,255,0.05)', display: 'flex', alignItems: 'center', justifyContent: 'center', border: '1px solid rgba(255,255,255,0.1)' }}>
                  <svg viewBox="0 0 24 24" width="24" height="24" stroke="currentColor" fill="none" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ color: '#60A5FA' }}>
                    <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" />
                    <polyline points="3.27 6.96 12 12.01 20.73 6.96" />
                    <line x1="12" y1="22.08" x2="12" y2="12" />
                  </svg>
                </div>
                <span className="badge badge-on">Active</span>
              </div>
              <h3 style={{ fontSize: '18px', fontWeight: 600, color: 'var(--g1-text)', marginBottom: '6px' }}>{t.iso_name}</h3>
              <p style={{ fontSize: '13px', color: 'var(--g1-muted)', marginBottom: '16px', lineHeight: '1.5' }}>
                Modèle Proxmox lié au VMID {t.proxmox_template_vmid}.
              </p>
              <div style={{ display: 'flex', gap: '16px', borderTop: '1px solid var(--g1-border)', paddingTop: '16px', alignItems: 'center' }}>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: '11px', color: 'var(--g1-muted)', textTransform: 'uppercase', marginBottom: '4px' }}>ID Interne</div>
                  <div style={{ fontSize: '13px', color: 'var(--g1-text)', fontWeight: 600 }}>{t.proxmox_template_vmid}</div>
                </div>
                <button className="btn-ghost" style={{ fontSize: '12px', padding: '6px 12px' }}>Mapper</button>
              </div>
            </div>
          ))}
          {templates.length === 0 && (
            <div style={{ gridColumn: '1 / -1', textAlign: 'center', padding: '40px', color: 'var(--g1-muted)' }}>
              Aucun template mappé. Associez une ISO à un VMID Proxmox.
            </div>
          )}
        </div>
      )}

      {/* ── ISO TAB ── */}
      {activeTab === 'isos' && (
        <div>
          {/* Upload call-to-action banner */}
          <div style={{
            display: 'flex', alignItems: 'center', gap: '16px',
            padding: '16px 20px', marginBottom: '20px',
            background: 'rgba(99,102,241,0.06)',
            border: '1px solid rgba(99,102,241,0.2)',
            borderRadius: '12px',
          }}>
            <div style={{ color: '#818CF8', flexShrink: 0 }}>
              <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" fill="none" strokeWidth="2">
                <circle cx="12" cy="12" r="10" />
                <line x1="12" y1="8" x2="12" y2="16" />
                <line x1="8" y1="12" x2="16" y2="12" />
              </svg>
            </div>
            <div style={{ flex: 1, fontSize: '13px', color: '#94A3B8', lineHeight: '1.5' }}>
              Vous pouvez <strong style={{ color: '#C7D2FE' }}>uploader directement un fichier .iso</strong> vers le stockage partagé Proxmox,
              ou simplement <strong style={{ color: '#C7D2FE' }}>référencer</strong> un ISO déjà présent sur le cluster.
            </div>
            <button
              onClick={() => setIsUploadModalOpen(true)}
              style={{
                flexShrink: 0, padding: '8px 16px',
                background: 'linear-gradient(135deg, #6366f1, #4f46e5)',
                border: 'none', color: 'white', borderRadius: '8px',
                fontSize: '12px', fontWeight: 600, cursor: 'pointer',
                display: 'flex', alignItems: 'center', gap: '6px',
              }}
            >
              <svg viewBox="0 0 24 24" width="13" height="13" stroke="currentColor" fill="none" strokeWidth="2.5">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                <polyline points="17 8 12 3 7 8" />
                <line x1="12" y1="3" x2="12" y2="15" />
              </svg>
              Uploader maintenant
            </button>
          </div>

          {/* ISO Table */}
          <div className="pm-card">
            <div className="pm-hdr">
              <svg viewBox="0 0 24 24" width="18" height="18" stroke="currentColor" fill="none" strokeWidth="2">
                <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
              </svg>
              Fichiers ISO enregistrés dans la base de données
            </div>
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
                <thead style={{ background: 'rgba(255,255,255,0.02)' }}>
                  <tr>
                    <th style={{ padding: '16px 20px', textAlign: 'left', color: 'var(--g1-muted)', fontWeight: 600 }}>Nom affiché</th>
                    <th style={{ padding: '16px 20px', textAlign: 'left', color: 'var(--g1-muted)', fontWeight: 600 }}>Fichier</th>
                    <th style={{ padding: '16px 20px', textAlign: 'left', color: 'var(--g1-muted)', fontWeight: 600 }}>OS</th>
                    <th style={{ padding: '16px 20px', textAlign: 'left', color: 'var(--g1-muted)', fontWeight: 600 }}>Statut</th>
                    <th style={{ padding: '16px 20px', textAlign: 'right', color: 'var(--g1-muted)', fontWeight: 600 }}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {isos.map(iso => (
                    <tr key={iso.id} style={{ transition: 'background 0.15s' }}>
                      <td style={{ padding: '14px 20px', borderBottom: '1px solid rgba(255,255,255,0.03)', color: 'white', fontWeight: 500 }}>{iso.name}</td>
                      <td style={{ padding: '14px 20px', borderBottom: '1px solid rgba(255,255,255,0.03)', color: 'var(--g1-muted)', fontFamily: 'monospace', fontSize: '12px' }}>{iso.filename}</td>
                      <td style={{ padding: '14px 20px', borderBottom: '1px solid rgba(255,255,255,0.03)', color: 'var(--g1-muted)' }}>{iso.os_family} {iso.os_version}</td>
                      <td style={{ padding: '14px 20px', borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
                        <span className={`badge ${iso.is_active ? 'badge-on' : 'badge-err'}`}>{iso.is_active ? 'ACTIF' : 'INACTIF'}</span>
                      </td>
                      <td style={{ padding: '14px 20px', borderBottom: '1px solid rgba(255,255,255,0.03)', textAlign: 'right' }}>
                        <button className="btn-ghost" style={{ fontSize: '11px' }}>Détails</button>
                      </td>
                    </tr>
                  ))}
                  {isos.length === 0 && (
                    <tr>
                      <td colSpan={5} style={{ padding: '40px', textAlign: 'center', color: 'var(--g1-muted)' }}>
                        Aucune image ISO enregistrée.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* ── MODAL: Register ISO in DB only ── */}
      {isIsoModalOpen && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, backgroundColor: 'rgba(15, 23, 42, 0.65)', backdropFilter: 'blur(4px)', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 1000, padding: '20px' }}>
          <div style={{ background: '#0F1623', borderRadius: '16px', width: '100%', maxWidth: '500px', border: '1px solid var(--g1-border)', boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.3)' }}>
            <div style={{ padding: '24px 32px 16px', borderBottom: '1px solid var(--g1-border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h2 style={{ fontSize: '20px', fontWeight: 'bold', color: '#F8FAFC', margin: 0 }}>Référencer une image ISO</h2>
              <button onClick={() => setIsIsoModalOpen(false)} style={{ background: 'none', border: 'none', color: '#64748B', cursor: 'pointer', padding: '4px' }}>
                <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" strokeWidth="2" fill="none"><line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" /></svg>
              </button>
            </div>
            <form onSubmit={handleAddIso} style={{ padding: '24px 32px' }}>
              <p style={{ fontSize: '13px', color: '#64748B', marginBottom: '16px', marginTop: 0 }}>
                Enregistre un ISO déjà présent sur le cluster dans la base de données SIGMA.
              </p>
              <div style={{ marginBottom: '16px' }}>
                <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, color: '#F8FAFC', marginBottom: '8px' }}>Nom d'affichage</label>
                <input required type="text" placeholder="Ex: Ubuntu 22.04 LTS" value={newName} onChange={e => setNewName(e.target.value)} style={{ width: '100%', padding: '10px 14px', background: 'rgba(255,255,255,0.03)', border: '1px solid var(--g1-border)', borderRadius: '8px', color: '#F8FAFC', fontSize: '14px', outline: 'none', boxSizing: 'border-box' }} />
              </div>
              <div style={{ marginBottom: '16px' }}>
                <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, color: '#F8FAFC', marginBottom: '8px' }}>Nom du fichier sur Proxmox</label>
                <input required type="text" placeholder="Ex: ubuntu-22.04-server.iso" value={newFilename} onChange={e => setNewFilename(e.target.value)} style={{ width: '100%', padding: '10px 14px', background: 'rgba(255,255,255,0.03)', border: '1px solid var(--g1-border)', borderRadius: '8px', color: '#F8FAFC', fontSize: '14px', outline: 'none', boxSizing: 'border-box' }} />
              </div>
              <div style={{ display: 'flex', gap: '16px', marginBottom: '16px' }}>
                <div style={{ flex: 1 }}>
                  <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, color: '#F8FAFC', marginBottom: '8px' }}>Famille OS</label>
                  <select value={osFamily} onChange={e => setOsFamily(e.target.value)} style={{ width: '100%', padding: '10px 14px', background: '#0F1623', border: '1px solid var(--g1-border)', borderRadius: '8px', color: '#F8FAFC', fontSize: '14px' }}>
                    <option value="Linux">Linux</option>
                    <option value="Windows">Windows</option>
                    <option value="BSD">BSD</option>
                    <option value="Other">Autre</option>
                  </select>
                </div>
                <div style={{ flex: 1 }}>
                  <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, color: '#F8FAFC', marginBottom: '8px' }}>Version</label>
                  <input required type="text" placeholder="Ex: 22.04" value={osVersion} onChange={e => setOsVersion(e.target.value)} style={{ width: '100%', padding: '10px 14px', background: 'rgba(255,255,255,0.03)', border: '1px solid var(--g1-border)', borderRadius: '8px', color: '#F8FAFC', fontSize: '14px', outline: 'none' }} />
                </div>
              </div>
              <div style={{ marginBottom: '24px' }}>
                <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, color: '#F8FAFC', marginBottom: '8px' }}>Description</label>
                <textarea placeholder="Brève description..." value={newDesc} onChange={e => setNewDesc(e.target.value)} style={{ width: '100%', padding: '10px 14px', background: 'rgba(255,255,255,0.03)', border: '1px solid var(--g1-border)', borderRadius: '8px', color: '#F8FAFC', fontSize: '14px', minHeight: '60px', boxSizing: 'border-box' }} />
              </div>
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
                <button type="button" onClick={() => setIsIsoModalOpen(false)} style={{ padding: '10px 18px', background: 'transparent', border: '1px solid var(--g1-border)', color: '#F8FAFC', borderRadius: '8px', fontSize: '14px', fontWeight: 600, cursor: 'pointer' }}>Annuler</button>
                <button type="submit" style={{ padding: '10px 18px', background: '#2563EB', border: 'none', color: '#fff', borderRadius: '8px', fontSize: '14px', fontWeight: 600, cursor: 'pointer' }}>Enregistrer</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ── MODAL: ISO Upload to Proxmox ── */}
      {isUploadModalOpen && (
        <IsoUploadModal
          onClose={() => setIsUploadModalOpen(false)}
          onSuccess={() => { fetchData(); }}
        />
      )}
      <Modal {...alertConfig} onClose={closeAlert} />
    </div>
  );
}
