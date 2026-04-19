"use client";
import { useRouter } from 'next/navigation';
import { useVMs } from './VMContext';
import { useAuth } from '../../context/AuthContext';

export default function DashboardHome() {
  const { vms } = useVMs();
  const { user } = useAuth();
  const router = useRouter();

  // Date dynamique
  const today = new Date().toLocaleDateString('fr-FR', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
    year: 'numeric'
  });

  const formattedDate = today.charAt(0).toUpperCase() + today.slice(1);

  // Compute stats
  const totalVMs = vms.length;
  // Les statuts valides pour une VM "active" sont ACTIVE et WARNING
  const activeVMs = vms.filter(v => ['ACTIVE', 'WARNING', 'running', 'on'].includes(v.status)).length;
  const totalCpu = vms.reduce((acc, v) => acc + (v.vcpu || 0), 0);
  const totalRam = vms.reduce((acc, v) => acc + (v.ram_gb || 0), 0);

  return (
    <div className="page active" id="pg-dashboard">
      <div className="welcome">
        <div className="welcome-left">
          <h2>Bonjour, {user?.first_name || 'Utilisateur'}</h2>
          <p>{formattedDate} · Cluster Horizon en ligne</p>
        </div>
        <div className="welcome-right">
          <button className="btn-ghost" onClick={() => router.push('/dashboard/mes-vms')}>Voir mes VMs</button>
          <button className="btn-accent" onClick={() => window.dispatchEvent(new Event('open-create-vm'))}>+ Nouvelle réservation</button>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '20px', marginTop: '10px' }}>

        <div className="vm-status-card">
          <div className="vsc-top">
            <div style={{ padding: '8px', background: 'rgba(37,99,235,0.1)', color: 'var(--g1-accent2)', borderRadius: '8px' }}>
              <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" strokeWidth="2" fill="none"><rect x="2" y="4" width="20" height="16" rx="2"></rect><path d="M8 4v16M16 4v16"></path></svg>
            </div>
            <span className="badge badge-blue">Global</span>
          </div>
          <div className="vsc-id" style={{ textTransform: 'uppercase', letterSpacing: '1px', fontSize: '10px' }}>Machines Virtuelles</div>
          <div className="vsc-name" style={{ fontSize: '32px', marginTop: '4px' }}>{totalVMs}</div>
          <div className="vsc-meta">Total des instances réservées</div>
        </div>

        <div className="vm-status-card">
          <div className="vsc-top">
            <div style={{ padding: '8px', background: 'rgba(16,185,129,0.1)', color: 'var(--g1-on)', borderRadius: '8px' }}>
              <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" strokeWidth="2" fill="none"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>
            </div>
            <span className="badge badge-on">Online</span>
          </div>
          <div className="vsc-id" style={{ textTransform: 'uppercase', letterSpacing: '1px', fontSize: '10px' }}>En Fonctionnement</div>
          <div className="vsc-name" style={{ fontSize: '32px', marginTop: '4px' }}>{activeVMs}</div>
          <div className="vsc-meta">VMs actives sur le cluster</div>
        </div>

        <div className="vm-status-card">
          <div className="vsc-top">
            <div style={{ padding: '8px', background: 'rgba(139,92,246,0.1)', color: '#8B5CF6', borderRadius: '8px' }}>
              <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" strokeWidth="2" fill="none"><rect x="4" y="4" width="16" height="16" rx="2" ry="2"></rect><rect x="9" y="9" width="6" height="6"></rect><line x1="9" y1="1" x2="9" y2="4"></line><line x1="15" y1="1" x2="15" y2="4"></line><line x1="9" y1="20" x2="9" y2="23"></line><line x1="15" y1="20" x2="15" y2="23"></line><line x1="20" y1="9" x2="23" y2="9"></line><line x1="20" y1="14" x2="23" y2="14"></line><line x1="1" y1="9" x2="4" y2="9"></line><line x1="1" y1="14" x2="4" y2="14"></line></svg>
            </div>
            <span className="badge badge-blue">vCPU</span>
          </div>
          <div className="vsc-id" style={{ textTransform: 'uppercase', letterSpacing: '1px', fontSize: '10px' }}>Ressources CPU</div>
          <div className="vsc-name" style={{ fontSize: '32px', marginTop: '4px' }}>{totalCpu}</div>
          <div className="vsc-meta">Cœurs virtuels alloués</div>
        </div>

        <div className="vm-status-card">
          <div className="vsc-top">
            <div style={{ padding: '8px', background: 'rgba(245,158,11,0.1)', color: 'var(--g1-warn)', borderRadius: '8px' }}>
              <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" strokeWidth="2" fill="none"><line x1="8" y1="6" x2="21" y2="6"></line><line x1="8" y1="12" x2="21" y2="12"></line><line x1="8" y1="18" x2="21" y2="18"></line><line x1="3" y1="6" x2="3.01" y2="6"></line><line x1="3" y1="12" x2="3.01" y2="12"></line><line x1="3" y1="18" x2="3.01" y2="18"></line></svg>
            </div>
            <span className="badge badge-warn">RAM</span>
          </div>
          <div className="vsc-id" style={{ textTransform: 'uppercase', letterSpacing: '1px', fontSize: '10px' }}>Mémoire Vive</div>
          <div className="vsc-name" style={{ fontSize: '32px', marginTop: '4px' }}>{totalRam} <span style={{ fontSize: '16px', color: 'var(--g1-muted)' }}>Go</span></div>
          <div className="vsc-meta">Mémoire totale provisionnée</div>
        </div>

      </div>

      {/* Recents VMs Section */}
      <div className="vm-panel" style={{ marginTop: '32px' }}>
        <div className="vm-panel-hdr">
          <div>
            <h3 className="vm-panel-title">Activités Récentes</h3>
            <p className="vm-panel-meta">Vos dernières machines virtuelles créées sur le cluster Horizon.</p>
          </div>
          <button className="btn-ghost" onClick={() => router.push('/dashboard/mes-vms')}>Tout voir</button>
        </div>
        <div className="act-list" style={{ padding: '20px 24px' }}>
          {vms.slice(0, 3).map(vm => (
            <div key={vm.id} className="act-item" onClick={() => router.push(`/dashboard/mes-vms/${vm.id}`)} style={{ cursor: 'pointer' }}>
              <div className={`act-dot ${['ACTIVE', 'running', 'on'].includes(vm.status) ? 'on' : (['STOPPED', 'off'].includes(vm.status) ? 'off' : 'warn')}`}
                style={{ background: ['ACTIVE', 'running', 'on'].includes(vm.status) ? 'var(--g1-on)' : (['STOPPED', 'off'].includes(vm.status) ? 'var(--g1-off)' : 'var(--g1-warn)') }}></div>
              <div className="act-content">
                <h4>{vm.name}</h4>
                <p>Status: {vm.status} · {vm.vcpu} vCPU · {vm.ram_gb} Go RAM · IP: {vm.ip_address || 'Allocation...'}</p>
              </div>
            </div>
          ))}
          {vms.length === 0 && (
            <p style={{ textAlign: 'center', padding: '20px', color: 'var(--g1-muted)' }}>Aucune activité récente.</p>
          )}
        </div>
      </div>
    </div>
  )
}
