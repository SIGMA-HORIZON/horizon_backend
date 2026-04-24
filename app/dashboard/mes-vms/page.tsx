"use client";
import { useRouter } from 'next/navigation';
import { useVMs } from '../VMContext';
import { Icon } from '@/components/Icon';

export default function MesVMs() {
  const router = useRouter();
  const { vms, startVM, stopVM } = useVMs();

  return (
    <div className="page active">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '32px' }}>
        <div>
          <h1 style={{ fontSize: '28px', fontWeight: '800', letterSpacing: '-0.5px' }}>Mes Machines Virtuelles</h1>
          <p style={{ color: 'var(--g1-muted)', marginTop: '4px', fontSize: '14px' }}>Gérez vos instances et surveillez leurs performances en temps réel.</p>
        </div>
        <button className="btn-accent" onClick={() => window.dispatchEvent(new Event('open-create-vm'))}>
          <Icon name="start" size={18} strokeWidth={3} style={{ marginRight: '8px', verticalAlign: 'middle', transform: 'rotate(90deg)' }} />
          Nouvelle VM
        </button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))', gap: '24px' }}>
        {vms.map(vm => {
          const isRunning = ['ACTIVE', 'running', 'on'].includes(vm.status);
          return (
            <div 
              key={vm.id} 
              className="vm-status-card" 
              onClick={() => router.push(`/dashboard/mes-vms/${vm.id}`)}
              style={{ padding: '0', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}
            >
              <div style={{ padding: '24px', flex: 1 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '20px' }}>
                  <div className="vm-hero-icon" style={{ width: '48px', height: '48px', borderRadius: '12px' }}>
                    <Icon name="vms" size={24} style={{ color: 'var(--g1-accent)' }} />
                  </div>
                  <span className={`badge ${isRunning ? 'badge-on' : (['STOPPED', 'off'].includes(vm.status) ? 'badge-off' : 'badge-warn')}`}>
                    {isRunning ? '● EN LIGNE' : '○ HORS LIGNE'}
                  </span>
                </div>

                <h3 style={{ fontSize: '18px', fontWeight: '700', marginBottom: '4px' }}>{vm.name}</h3>
                <p style={{ fontSize: '12px', color: 'var(--g1-muted)', marginBottom: '20px', fontFamily: 'monospace' }}>IP: {vm.ip_address || 'Allocation...'}</p>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '20px' }}>
                  <div style={{ background: 'rgba(255,255,255,0.03)', padding: '10px', borderRadius: '8px', border: '1px solid var(--g1-border)' }}>
                    <div style={{ fontSize: '10px', color: 'var(--g1-muted)', textTransform: 'uppercase', fontWeight: '700' }}>vCPU</div>
                    <div style={{ fontSize: '14px', fontWeight: '600', marginTop: '2px' }}>{vm.vcpu} Cores</div>
                  </div>
                  <div style={{ background: 'rgba(255,255,255,0.03)', padding: '10px', borderRadius: '8px', border: '1px solid var(--g1-border)' }}>
                    <div style={{ fontSize: '10px', color: 'var(--g1-muted)', textTransform: 'uppercase', fontWeight: '700' }}>RAM</div>
                    <div style={{ fontSize: '14px', fontWeight: '600', marginTop: '2px' }}>{vm.ram_gb} Go</div>
                  </div>
                </div>

                <div className="stat-card-footer" style={{ marginTop: 'auto', paddingTop: '16px', borderTop: '1px solid var(--g1-border)' }}>
                   <Icon name="vms" size={14} />
                   Linux Ubuntu 22.04
                </div>
              </div>

              <div style={{ display: 'flex', borderTop: '1px solid var(--g1-border)', background: 'rgba(255,255,255,0.02)' }} onClick={e => e.stopPropagation()}>
                <button 
                  className="btn-vm" 
                  style={{ flex: 1, border: 'none', borderRadius: '0', padding: '14px', justifyContent: 'center', borderRight: '1px solid var(--g1-border)' }}
                  onClick={() => router.push(`/dashboard/mes-vms/${vm.id}/console`)}
                >
                  <Icon name="console" />
                  Console
                </button>
                {isRunning ? (
                  <button 
                    className="btn-vm btn-vm-stop" 
                    style={{ flex: 1, border: 'none', borderRadius: '0', padding: '14px', justifyContent: 'center' }}
                    onClick={() => stopVM(vm.id)}
                  >
                    <Icon name="stop" />
                    Arrêter
                  </button>
                ) : (
                  <button 
                    className="btn-vm btn-vm-start" 
                    style={{ flex: 1, border: 'none', borderRadius: '0', padding: '14px', justifyContent: 'center' }}
                    onClick={() => startVM(vm.id)}
                  >
                    <Icon name="start" />
                    Démarrer
                  </button>
                )}
              </div>
            </div>
          );
        })}
        {vms.length === 0 && (
          <div style={{ gridColumn: '1 / -1', padding: '80px', textAlign: 'center', background: 'var(--g1-card)', borderRadius: '16px', border: '1px dashed var(--g1-border)' }}>
             <div style={{ fontSize: '48px', marginBottom: '20px' }}>📦</div>
             <h3 style={{ fontSize: '20px', fontWeight: '700', color: '#fff' }}>Aucune VM pour le moment</h3>
             <p style={{ color: 'var(--g1-muted)', marginTop: '8px' }}>Commencez par créer votre première machine virtuelle en quelques clics.</p>
             <button className="btn-accent" style={{ marginTop: '24px' }} onClick={() => window.dispatchEvent(new Event('open-create-vm'))}>Créer une VM</button>
          </div>
        )}
      </div>
    </div>
  )
}
