"use client";
import { useRouter } from 'next/navigation';
import { useVMs } from '../VMContext';

export default function MesVMs() {
  const router = useRouter();
  const { vms } = useVMs();

  return (
    <div className="page active">
      <div style={{ paddingBottom: '20px' }}>
        <h1 style={{ fontSize: '24px', fontWeight: 'bold' }}>Mes VMs</h1>
        <button className="btn-accent" style={{ marginTop: '5px' }} onClick={() => window.dispatchEvent(new Event('open-create-vm'))}>+ Créer une VM</button>
      </div>

      <div className="vm-panel" style={{ marginBottom: '14px' }}>
        <table>
          <thead style={{ background: '#F8FAFD' }}>
            <tr>
              <th style={{ padding: '10px 16px' }}>VM</th>
              <th>Statut</th>
              <th>OS</th>
              <th>CPU</th>
              <th>RAM</th>
              <th>IP</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {vms.map(vm => (
              <tr key={vm.id} onClick={() => router.push(`/dashboard/mes-vms/${vm.id}`)} style={{ cursor: 'pointer' }}>
                <td style={{ padding: '10px 16px' }}>
                  <div style={{ fontWeight: 600, fontSize: '13px', color: 'var(--g1-text)' }}>{vm.name}</div>
                  <div style={{ fontSize: '10px', color: 'var(--g1-muted)' }}>{vm.id.slice(0, 8)}...</div>
                </td>
                <td>
                  <span className={`badge ${['ACTIVE', 'running', 'on'].includes(vm.status) ? 'badge-on' : (['STOPPED', 'off'].includes(vm.status) ? 'badge-off' : 'badge-warn')}`}>
                    {['ACTIVE', 'running', 'on'].includes(vm.status) ? '● ' : '○ '}
                    {vm.status.toUpperCase()}
                  </span>
                </td>
                <td><span className="badge badge-blue">LINUX</span></td>
                <td>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '12px' }}>
                    {vm.vcpu} vCPU
                  </div>
                </td>
                <td style={{ fontSize: '12px' }}>{vm.ram_gb} Go</td>
                <td style={{ fontSize: '11px', fontFamily: 'monospace', color: 'var(--g1-muted)' }}>{vm.ip_address || 'Allocation...'}</td>
                <td>
                  <div style={{ display: 'flex', gap: '8px' }} onClick={e => e.stopPropagation()}>
                    <button className="btn-vm" style={{ padding: '6px 10px', fontSize: '11px' }} onClick={() => router.push(`/dashboard/mes-vms/${vm.id}`)}>
                      <svg viewBox="0 0 24 24" width="14" height="14" stroke="currentColor" fill="none" strokeWidth="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" /><circle cx="12" cy="12" r="3" /></svg>
                      Détails
                    </button>
                    {['ACTIVE', 'running', 'on'].includes(vm.status) ? (
                      <button className="btn-vm btn-vm-stop" style={{ padding: '6px 10px', fontSize: '11px' }}>Arrêter</button>
                    ) : (
                      <button className="btn-vm btn-vm-start" style={{ padding: '6px 10px', fontSize: '11px' }}>Démarrer</button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
            {vms.length === 0 && (
              <tr>
                <td colSpan={7} style={{ textAlign: 'center', padding: '32px', color: 'var(--text-muted)' }}>
                  Aucune machine virtuelle trouvée.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
