"use client";
import React, { useEffect, useState } from 'react';
import { adminService } from '../../../services/admin';

export default function Reservations() {
  const [reservations, setReservations] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchReservations = async () => {
      try {
        const data = await adminService.listReservations();
        setReservations(data.items || []);
      } catch (err) {
        console.error("Erreur lors de la récupération des réservations:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchReservations();
  }, []);

  return (
    <div className="page active" style={{ padding: '0 20px 40px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '32px' }}>
        <div>
          <h1 style={{ fontSize: '24px', fontWeight: 700, color: 'var(--g1-text)', marginBottom: '4px', letterSpacing: '-0.5px' }}>Journal des réservations</h1>
          <p style={{ color: 'var(--g1-muted)', fontSize: '14px' }}>Historique et état actuel des sessions de machines virtuelles.</p>
        </div>
      </div>

      <div className="pm-card">
        <div className="pm-hdr">
          <svg viewBox="0 0 24 24" width="18" height="18" stroke="currentColor" fill="none" strokeWidth="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><polyline points="14 2 14 8 20 8" /><line x1="16" y1="13" x2="8" y2="13" /><line x1="16" y1="17" x2="8" y2="17" /><polyline points="10 9 9 9 8 9" /></svg>
          Liste des sessions
        </div>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
            <thead style={{ background: 'rgba(255,255,255,0.02)' }}>
              <tr>
                <th style={{ padding: '16px 20px', textAlign: 'left', color: 'var(--g1-muted)', fontWeight: 600, borderBottom: '1px solid var(--g1-border)' }}>Utilisateur & VM</th>
                <th style={{ padding: '16px 20px', textAlign: 'left', color: 'var(--g1-muted)', fontWeight: 600, borderBottom: '1px solid var(--g1-border)' }}>OS / Image</th>
                <th style={{ padding: '16px 20px', textAlign: 'left', color: 'var(--g1-muted)', fontWeight: 600, borderBottom: '1px solid var(--g1-border)' }}>Ressources</th>
                <th style={{ padding: '16px 20px', textAlign: 'left', color: 'var(--g1-muted)', fontWeight: 600, borderBottom: '1px solid var(--g1-border)' }}>Durée & Création</th>
                <th style={{ padding: '16px 20px', textAlign: 'left', color: 'var(--g1-muted)', fontWeight: 600, borderBottom: '1px solid var(--g1-border)' }}>Statut</th>
                <th style={{ padding: '16px 20px', textAlign: 'right', color: 'var(--g1-muted)', fontWeight: 600, borderBottom: '1px solid var(--g1-border)' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={6} style={{ padding: '40px', textAlign: 'center', color: 'var(--g1-muted)' }}>Chargement...</td></tr>
              ) : reservations.length === 0 ? (
                <tr><td colSpan={6} style={{ padding: '40px', textAlign: 'center', color: 'var(--g1-muted)' }}>Aucune réservation trouvée.</td></tr>
              ) : (
                reservations.map((res: any) => (
                  <tr key={res.id}>
                    <td style={{ padding: '16px 20px', borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
                      <div style={{ fontWeight: 600, color: 'var(--g1-text)' }}>{res.user_full_name}</div>
                      <div style={{ fontSize: '11px', color: 'var(--g1-muted)' }}>{res.vm_name}</div>
                    </td>
                    <td style={{ padding: '16px 20px', borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
                      <span className="badge badge-blue" style={{ background: 'rgba(59,130,246,0.1)', color: '#60A5FA', border: '1px solid rgba(59,130,246,0.2)' }}>{res.os_name}</span>
                    </td>
                    <td style={{ padding: '16px 20px', borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
                      <div style={{ color: 'var(--g1-text)' }}>{res.vcpu} vCPU · {res.ram_gb} Go</div>
                      <div style={{ fontSize: '11px', color: 'var(--g1-muted)' }}>{res.storage_gb} Go SSD</div>
                    </td>
                    <td style={{ padding: '16px 20px', borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
                      <div style={{ color: 'var(--g1-text)' }}>{res.duration_hours} heures</div>
                      <div style={{ fontSize: '11px', color: 'var(--g1-muted)' }}>Le {new Date(res.created_at).toLocaleDateString()}</div>
                    </td>
                    <td style={{ padding: '16px 20px', borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
                      <span className={`badge ${res.status === 'ACTIVE' ? 'badge-on' : 'badge-err'}`}>{res.status}</span>
                    </td>
                    <td style={{ padding: '16px 20px', borderBottom: '1px solid rgba(255,255,255,0.03)', textAlign: 'right' }}>
                      <button className="btn-ghost" style={{ fontSize: '11px', padding: '4px 10px' }}>Détails</button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
