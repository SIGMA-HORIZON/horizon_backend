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
                  <div style={{ fontWeight: 600, fontSize: '12px' }}>{vm.name}</div>
                  <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>VMID {vm.id}</div>
                </td>
                <td>
                  <span className={`badge badge-${vm.status}`}>
                    {vm.status === 'warn' ? '⚠ ' : '● '}
                    {vm.statusText}
                  </span>
                </td>
                <td><span className="badge badge-blue">{vm.os}</span></td>
                <td>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '12px' }}>
                    {vm.cpuVal}%
                    <div className="mini-bar">
                      <div className={`mini-fill ${vm.status === 'warn' ? 'mini-fill-err' : (vm.cpuVal > 50 ? 'mini-fill-warn' : '')}`} style={{ width: `${vm.cpuVal}%` }}></div>
                    </div>
                  </div>
                </td>
                <td style={{ fontSize: '12px' }}>{((vm.ramVal / 100) * parseFloat(vm.ram)).toFixed(1)} / {vm.ram}</td>
                <td style={{ fontSize: '11px', fontFamily: 'monospace', color: 'var(--text-muted)' }}>{vm.ip}</td>
                <td>
                  <div style={{ display: 'flex', gap: '4px' }} onClick={e => e.stopPropagation()}>
                    <button className="btn-vm btn-vm-console" style={{ fontSize: '10px', padding: '3px 8px' }}>Console</button>
                    <button className="btn-vm btn-vm-stop" style={{ fontSize: '10px', padding: '3px 8px' }}>Stop</button>
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
