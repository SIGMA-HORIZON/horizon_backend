"use client";
import React from 'react';

export default function Reservations() {
  return (
    <div className="page active" style={{ padding: '0 20px 40px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '32px' }}>
        <div>
          <h1 style={{ fontSize: '24px', fontWeight: 700, color: 'var(--g1-text)', marginBottom: '4px', letterSpacing: '-0.5px' }}>Demandes de réservation</h1>
          <p style={{ color: 'var(--g1-muted)', fontSize: '14px' }}>Valider ou rejeter les allocations de ressources pour les utilisateurs.</p>
        </div>
        <div style={{ display: 'flex', padding: '4px', background: 'rgba(255,255,255,0.05)', borderRadius: '8px', border: '1px solid var(--g1-border)' }}>
          <button style={{ background: 'var(--g1-accent2)', color: '#fff', border: 'none', padding: '8px 16px', borderRadius: '6px', fontSize: '13px', fontWeight: 500, cursor: 'pointer' }}>En attente</button>
          <button style={{ background: 'transparent', color: 'var(--g1-muted)', border: 'none', padding: '8px 16px', borderRadius: '6px', fontSize: '13px', fontWeight: 500, cursor: 'pointer' }}>Toutes</button>
          <button style={{ background: 'transparent', color: 'var(--g1-muted)', border: 'none', padding: '8px 16px', borderRadius: '6px', fontSize: '13px', fontWeight: 500, cursor: 'pointer' }}>Résolues</button>
        </div>
      </div>

      <div className="pm-card">
        <div className="pm-hdr">
          <svg viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>
          Dossiers en attente d'approbation
        </div>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
            <thead style={{ background: 'rgba(255,255,255,0.02)' }}>
              <tr>
                <th style={{ padding: '16px 20px', textAlign: 'left', color: 'var(--g1-muted)', fontWeight: 600, borderBottom: '1px solid var(--g1-border)' }}>Utilisateur & ID</th>
                <th style={{ padding: '16px 20px', textAlign: 'left', color: 'var(--g1-muted)', fontWeight: 600, borderBottom: '1px solid var(--g1-border)' }}>OS / Image</th>
                <th style={{ padding: '16px 20px', textAlign: 'left', color: 'var(--g1-muted)', fontWeight: 600, borderBottom: '1px solid var(--g1-border)' }}>Ressources</th>
                <th style={{ padding: '16px 20px', textAlign: 'left', color: 'var(--g1-muted)', fontWeight: 600, borderBottom: '1px solid var(--g1-border)' }}>Durée & Demande</th>
                <th style={{ padding: '16px 20px', textAlign: 'left', color: 'var(--g1-muted)', fontWeight: 600, borderBottom: '1px solid var(--g1-border)' }}>Statut</th>
                <th style={{ padding: '16px 20px', textAlign: 'right', color: 'var(--g1-muted)', fontWeight: 600, borderBottom: '1px solid var(--g1-border)' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {/* Reservation 1 */}
              <tr>
                <td style={{ padding: '16px 20px', borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
                  <div style={{ fontWeight: 600, color: 'var(--g1-text)' }}>Ornella Mbo'o</div>
                  <div style={{ fontSize: '12px', color: 'var(--g1-muted)' }}>vm-gpu-ornella-03</div>
                </td>
                <td style={{ padding: '16px 20px', borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
                  <span className="badge badge-blue">Ubuntu 22.04</span>
                </td>
                <td style={{ padding: '16px 20px', borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
                  <div style={{ color: 'var(--g1-text)' }}>16 vCPU · 64 Go</div>
                  <div style={{ fontSize: '12px', color: 'var(--g1-muted)' }}>2 GPU · 200 Go SSD</div>
                </td>
                <td style={{ padding: '16px 20px', borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
                  <div style={{ color: 'var(--g1-text)' }}>120 heures</div>
                  <div style={{ fontSize: '12px', color: 'var(--g1-muted)' }}>Demandé le 27/03/2026</div>
                </td>
                <td style={{ padding: '16px 20px', borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
                  <span className="badge badge-warn">En attente</span>
                </td>
                <td style={{ padding: '16px 20px', borderBottom: '1px solid rgba(255,255,255,0.03)', textAlign: 'right' }}>
                  <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
                    <button className="btn-ghost" style={{ fontSize: '12px', padding: '6px 12px', color: 'var(--g1-on)', borderColor: 'rgba(16,185,129,0.3)' }}>Approuver</button>
                    <button className="btn-ghost" style={{ fontSize: '12px', padding: '6px 12px', color: 'var(--g1-err)', borderColor: 'rgba(239,68,68,0.3)' }}>Rejeter</button>
                  </div>
                </td>
              </tr>

              {/* Reservation 2 */}
              <tr>
                <td style={{ padding: '16px 20px', borderBottom: 'none' }}>
                  <div style={{ fontWeight: 600, color: 'var(--g1-text)' }}>Jean Dupont</div>
                  <div style={{ fontSize: '12px', color: 'var(--g1-muted)' }}>vm-dev-dupont-02</div>
                </td>
                <td style={{ padding: '16px 20px', borderBottom: 'none' }}>
                  <span className="badge badge-blue">Debian 12</span>
                </td>
                <td style={{ padding: '16px 20px', borderBottom: 'none' }}>
                  <div style={{ color: 'var(--g1-text)' }}>4 vCPU · 8 Go</div>
                  <div style={{ fontSize: '12px', color: 'var(--g1-muted)' }}>0 GPU · 50 Go SSD</div>
                </td>
                <td style={{ padding: '16px 20px', borderBottom: 'none' }}>
                  <div style={{ color: 'var(--g1-text)' }}>48 heures</div>
                  <div style={{ fontSize: '12px', color: 'var(--g1-muted)' }}>Demandé le 27/03/2026</div>
                </td>
                <td style={{ padding: '16px 20px', borderBottom: 'none' }}>
                  <span className="badge badge-warn">En attente</span>
                </td>
                <td style={{ padding: '16px 20px', borderBottom: 'none', textAlign: 'right' }}>
                  <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
                    <button className="btn-ghost" style={{ fontSize: '12px', padding: '6px 12px', color: 'var(--g1-on)', borderColor: 'rgba(16,185,129,0.3)' }}>Approuver</button>
                    <button className="btn-ghost" style={{ fontSize: '12px', padding: '6px 12px', color: 'var(--g1-err)', borderColor: 'rgba(239,68,68,0.3)' }}>Rejeter</button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

    </div>
  )
}
