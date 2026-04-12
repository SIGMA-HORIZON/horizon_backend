"use client";
import { useRouter } from 'next/navigation';
import { useVMs } from './VMContext';

export default function DashboardHome() {
  const { vms } = useVMs();
  const router = useRouter();

  // Compute stats
  const totalVMs = vms.length;
  const activeVMs = vms.filter(v => v.status === 'on' || v.status === 'warn').length;
  const totalCpu = vms.reduce((acc, v) => acc + v.cpu, 0);
  const totalRam = vms.reduce((acc, v) => acc + parseFloat(v.ram), 0);

  const statCardStyle = {
    background: '#fff',
    border: '1px solid #E2E8F0',
    borderRadius: '12px',
    padding: '24px',
    boxShadow: '0 4px 6px -1px rgba(0,0,0,0.02)',
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '8px'
  };

  const statIconWrapStyle = {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    width: '40px',
    height: '40px',
    borderRadius: '8px',
    background: 'rgba(37,99,235,0.1)',
    color: '#2563EB',
    marginBottom: '8px'
  };

  const statLabelStyle = {
    fontSize: '14px',
    fontWeight: 600,
    color: '#64748B'
  };

  const statValueStyle = {
    fontSize: '32px',
    fontWeight: 'bold',
    color: '#0F172A',
    lineHeight: '1'
  };

  return (
    <div className="page active">

      <div className="page active" id="pg-dashboard">
        <div className="welcome">
          <div className="welcome-left">
            <h2>Bonjour, Ornella</h2>
            <p>Vendredi 27 mars 2026 · Cluster Horizon en ligne</p>
          </div>
          <div className="welcome-right">
            <button className="btn-ghost" onClick={() => router.push('/dashboard/mes-vms')}>Voir mes VMs</button>
            <button className="btn-accent" onClick={() => router.push('/dashboard/reservations')}>+ Nouvelle réservation</button>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '20px', marginTop: '10px' }}>
          
          <div style={statCardStyle}>
            <div style={statIconWrapStyle}>
              <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" strokeWidth="2" fill="none"><rect x="2" y="4" width="20" height="16" rx="2"></rect><path d="M8 4v16M16 4v16"></path></svg>
            </div>
            <div style={statLabelStyle}>Total des VMs</div>
            <div style={statValueStyle}>{totalVMs}</div>
          </div>

          <div style={statCardStyle}>
            <div style={{ ...statIconWrapStyle, background: 'rgba(16,185,129,0.1)', color: '#10B981' }}>
              <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" strokeWidth="2" fill="none"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>
            </div>
            <div style={statLabelStyle}>VMs Actives</div>
            <div style={statValueStyle}>{activeVMs}</div>
          </div>

          <div style={statCardStyle}>
            <div style={{ ...statIconWrapStyle, background: 'rgba(139,92,246,0.1)', color: '#8B5CF6' }}>
              <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" strokeWidth="2" fill="none"><rect x="4" y="4" width="16" height="16" rx="2" ry="2"></rect><rect x="9" y="9" width="6" height="6"></rect><line x1="9" y1="1" x2="9" y2="4"></line><line x1="15" y1="1" x2="15" y2="4"></line><line x1="9" y1="20" x2="9" y2="23"></line><line x1="15" y1="20" x2="15" y2="23"></line><line x1="20" y1="9" x2="23" y2="9"></line><line x1="20" y1="14" x2="23" y2="14"></line><line x1="1" y1="9" x2="4" y2="9"></line><line x1="1" y1="14" x2="4" y2="14"></line></svg>
            </div>
            <div style={statLabelStyle}>vCPU Alloués</div>
            <div style={statValueStyle}>{totalCpu}</div>
          </div>

          <div style={statCardStyle}>
            <div style={{ ...statIconWrapStyle, background: 'rgba(245,158,11,0.1)', color: '#F59E0B' }}>
              <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" strokeWidth="2" fill="none"><line x1="8" y1="6" x2="21" y2="6"></line><line x1="8" y1="12" x2="21" y2="12"></line><line x1="8" y1="18" x2="21" y2="18"></line><line x1="3" y1="6" x2="3.01" y2="6"></line><line x1="3" y1="12" x2="3.01" y2="12"></line><line x1="3" y1="18" x2="3.01" y2="18"></line></svg>
            </div>
            <div style={statLabelStyle}>RAM Allouée</div>
            <div style={statValueStyle}>{totalRam} <span style={{fontSize: '18px', color: '#64748B'}}>Go</span></div>
          </div>

        </div>

      </div>
    </div>
  )
}
