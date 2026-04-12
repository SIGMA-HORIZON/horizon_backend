"use client";
import React, { useState } from 'react';

export default function Noeuds() {
  const [nodes, setNodes] = useState([
    { id: 1, name: 'node-01', ip: '10.0.0.11', status: 'badge-on', statusText: 'En ligne', cpu: 72, cpuColor: 'var(--g1-warn)', ram: 54, ramText: '64 / 128 Go', vms: 8 },
    { id: 2, name: 'node-02', ip: '10.0.0.12', status: 'badge-on', statusText: 'En ligne', cpu: 45, cpuColor: '', ram: 30, ramText: '38 / 128 Go', vms: 5 },
    { id: 3, name: 'node-gpu-01', ip: '10.0.0.15', status: 'badge-warn', statusText: 'Surchargé', cpu: 96, cpuColor: 'var(--g1-err)', ram: 82, ramText: '210 / 256 Go', vms: 14 }
  ]);

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [newName, setNewName] = useState('');
  const [newIp, setNewIp] = useState('');
  const [newRam, setNewRam] = useState('128 Go');

  const handleAddNode = (e: React.FormEvent) => {
    e.preventDefault();
    const newNode = {
      id: Date.now(),
      name: newName || 'node-new',
      ip: newIp || '10.0.x.x',
      status: 'badge-on',
      statusText: 'Prêt',
      cpu: 0,
      cpuColor: '',
      ram: 0,
      ramText: `0 / ${newRam}`,
      vms: 0
    };
    setNodes([...nodes, newNode]);
    setIsModalOpen(false);
    setNewName('');
    setNewIp('');
    setNewRam('128 Go');
  };

  return (
    <div className="page active" style={{ padding: '0 20px 40px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '32px' }}>
        <div>
          <h1 style={{ fontSize: '24px', fontWeight: 700, color: 'var(--g1-text)', marginBottom: '4px', letterSpacing: '-0.5px' }}>Nœuds du Cluster</h1>
          <p style={{ color: 'var(--g1-muted)', fontSize: '14px' }}>Supervision de l'état des hyperviseurs et gestion matérielle.</p>
        </div>
        <button className="btn-accent" onClick={() => setIsModalOpen(true)} style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '10px 18px', fontSize: '14px' }}>
          <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" fill="none" strokeWidth="2.5"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
          Enregistrer un nœud
        </button>
      </div>

      <div className="pm-card">
        <div className="pm-hdr">
          <svg viewBox="0 0 24 24"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
          Liste des hyperviseurs physiques
        </div>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
            <thead style={{ background: 'rgba(255,255,255,0.02)' }}>
              <tr>
                <th style={{ padding: '16px 20px', textAlign: 'left', color: 'var(--g1-muted)', fontWeight: 600, borderBottom: '1px solid var(--g1-border)' }}>Nom / IP</th>
                <th style={{ padding: '16px 20px', textAlign: 'left', color: 'var(--g1-muted)', fontWeight: 600, borderBottom: '1px solid var(--g1-border)' }}>Statut</th>
                <th style={{ padding: '16px 20px', textAlign: 'left', color: 'var(--g1-muted)', fontWeight: 600, borderBottom: '1px solid var(--g1-border)' }}>Charge CPU</th>
                <th style={{ padding: '16px 20px', textAlign: 'left', color: 'var(--g1-muted)', fontWeight: 600, borderBottom: '1px solid var(--g1-border)' }}>Mémoire (RAM)</th>
                <th style={{ padding: '16px 20px', textAlign: 'left', color: 'var(--g1-muted)', fontWeight: 600, borderBottom: '1px solid var(--g1-border)' }}>VMs</th>
                <th style={{ padding: '16px 20px', textAlign: 'left', color: 'var(--g1-muted)', fontWeight: 600, borderBottom: '1px solid var(--g1-border)', textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {nodes.map((node, i) => (
                <tr key={node.id}>
                  <td style={{ padding: '16px 20px', borderBottom: i === nodes.length -1 ? 'none' : '1px solid rgba(255,255,255,0.03)' }}>
                    <div style={{ fontWeight: 600, color: 'var(--g1-text)' }}>{node.name}</div>
                    <div style={{ fontSize: '12px', color: 'var(--g1-muted)', fontFamily: 'monospace' }}>{node.ip}</div>
                  </td>
                  <td style={{ padding: '16px 20px', borderBottom: i === nodes.length -1 ? 'none' : '1px solid rgba(255,255,255,0.03)' }}>
                    <span className={`badge ${node.status}`}>{node.statusText}</span>
                  </td>
                  <td style={{ padding: '16px 20px', borderBottom: i === nodes.length -1 ? 'none' : '1px solid rgba(255,255,255,0.03)' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{ width: '30px' }}>{node.cpu}%</span>
                      <div className="mini-bar"><div className="mini-fill" style={{ width: `${node.cpu}%`, background: node.cpuColor }}></div></div>
                    </div>
                  </td>
                  <td style={{ padding: '16px 20px', borderBottom: i === nodes.length -1 ? 'none' : '1px solid rgba(255,255,255,0.03)' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{ width: '30px' }}>{node.ram}%</span>
                      <div className="mini-bar"><div className="mini-fill" style={{ width: `${node.ram}%` }}></div></div>
                    </div>
                    <div style={{ fontSize: '11px', color: 'var(--g1-muted)', marginTop: '4px' }}>{node.ramText}</div>
                  </td>
                  <td style={{ padding: '16px 20px', borderBottom: i === nodes.length -1 ? 'none' : '1px solid rgba(255,255,255,0.03)', color: 'var(--g1-text)' }}>{node.vms} actives</td>
                  <td style={{ padding: '16px 20px', borderBottom: i === nodes.length -1 ? 'none' : '1px solid rgba(255,255,255,0.03)', textAlign: 'right' }}>
                    <button className="btn-ghost" style={{ fontSize: '12px', padding: '6px 12px' }}>Maintenance</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {isModalOpen && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, backgroundColor: 'rgba(15, 23, 42, 0.65)', backdropFilter: 'blur(4px)', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 1000, padding: '20px' }}>
          <div style={{ background: '#0F1623', borderRadius: '16px', width: '100%', maxWidth: '450px', border: '1px solid var(--g1-border)', boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.3)' }}>
            <div style={{ padding: '24px 32px 16px', borderBottom: '1px solid var(--g1-border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h2 style={{ fontSize: '20px', fontWeight: 'bold', color: '#F8FAFC', margin: 0 }}>Enregistrer un nœud</h2>
              <button onClick={() => setIsModalOpen(false)} style={{ background: 'none', border: 'none', color: '#64748B', cursor: 'pointer', padding: '4px' }}>
                <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" strokeWidth="2" fill="none"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
              </button>
            </div>
            <form onSubmit={handleAddNode} style={{ padding: '24px 32px' }}>
              <div style={{ marginBottom: '20px' }}>
                <label style={{ display: 'block', fontSize: '14px', fontWeight: 600, color: '#F8FAFC', marginBottom: '8px' }}>Nom d'hôte</label>
                <input required type="text" placeholder="Ex: node-03" value={newName} onChange={e => setNewName(e.target.value)} style={{ width: '100%', padding: '10px 14px', background: 'rgba(255,255,255,0.03)', border: '1px solid var(--g1-border)', borderRadius: '8px', color: '#F8FAFC', fontSize: '14px', outline: 'none' }} />
              </div>
              <div style={{ marginBottom: '20px' }}>
                <label style={{ display: 'block', fontSize: '14px', fontWeight: 600, color: '#F8FAFC', marginBottom: '8px' }}>Adresse IP</label>
                <input required type="text" placeholder="Ex: 10.0.0.13" value={newIp} onChange={e => setNewIp(e.target.value)} style={{ width: '100%', padding: '10px 14px', background: 'rgba(255,255,255,0.03)', border: '1px solid var(--g1-border)', borderRadius: '8px', color: '#F8FAFC', fontSize: '14px', outline: 'none' }} />
              </div>
              <div style={{ marginBottom: '32px' }}>
                <label style={{ display: 'block', fontSize: '14px', fontWeight: 600, color: '#F8FAFC', marginBottom: '8px' }}>Mémoire Totale (Go)</label>
                <input required type="text" placeholder="Ex: 128 Go" value={newRam} onChange={e => setNewRam(e.target.value)} style={{ width: '100%', padding: '10px 14px', background: 'rgba(255,255,255,0.03)', border: '1px solid var(--g1-border)', borderRadius: '8px', color: '#F8FAFC', fontSize: '14px', outline: 'none' }} />
              </div>
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
                <button type="button" onClick={() => setIsModalOpen(false)} style={{ padding: '10px 18px', background: 'transparent', border: '1px solid var(--g1-border)', color: '#F8FAFC', borderRadius: '8px', fontSize: '14px', fontWeight: 600, cursor: 'pointer' }}>Annuler</button>
                <button type="submit" style={{ padding: '10px 18px', background: '#2563EB', border: 'none', color: '#fff', borderRadius: '8px', fontSize: '14px', fontWeight: 600, cursor: 'pointer' }}>Enregistrer</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
