"use client";
import { useParams, useRouter } from 'next/navigation';
import { useState } from 'react';
import { useVMs } from '../../VMContext';
import { vmService } from '@/services/vms';
import { Icon } from '@/components/Icon';

export default function VMDetails() {
  const params = useParams();
  const router = useRouter();
  const vmid = params.vmid as string;
  const { vms, deleteVM, updateVM, startVM, stopVM, rebootVM, refreshVMs } = useVMs();

  const [editingField, setEditingField] = useState<string | null>(null);
  const [editValue, setEditValue] = useState<string>('');

  const vm = vms.find(v => v.id === vmid);

  if (!vm) return <VMNotFound vmid={vmid} onBack={() => router.push('/dashboard/mes-vms')} />;

  const isRunning = ['ACTIVE', 'running', 'on'].includes(vm.status);

  const handleEdit = (field: string, val: any) => {
    setEditingField(field);
    setEditValue(String(val));
  };

  const saveEdit = () => {
    if (!editingField || !editValue) return;
    const payload: any = { [editingField]: editingField === 'name' ? editValue : Number(editValue) };
    updateVM(vm.id, payload);
    setEditingField(null);
  };

  const downloadKey = async () => {
    try {
      const data = await vmService.getSshKey(vm.id);
      const blob = new Blob([data.ssh_public_key], { type: 'text/plain' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `horizon-${vm.name}.pub`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      alert("Clé SSH téléchargée avec succès. Elle a été supprimée du serveur.");
      refreshVMs();
    } catch (error: any) {
      alert(error.response?.data?.detail || "Erreur lors du téléchargement.");
    }
  };

  return (
    <div className="page active vm-details-layout">
      {/* 1. HERO SECTION */}
      <div className="vm-hero">
        <div className="vm-hero-left">
          <div className="vm-hero-icon">
            <Icon name="vms" size={24} />
          </div>
          <div className="vm-hero-info">
            <h1>{vm.name}</h1>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginTop: '4px' }}>
              <span className={`badge ${isRunning ? 'badge-on' : 'badge-off'}`}>
                {isRunning ? '● EN LIGNE' : '○ HORS LIGNE'}
              </span>
              <span style={{ color: 'var(--g1-muted)', fontSize: '13px' }}>ID: {vm.proxmox_vmid}</span>
            </div>
          </div>
        </div>

        <div className="vm-actions">
          <button className="btn-accent" onClick={() => router.push(`/dashboard/mes-vms/${vm.id}/console`)}>
            <Icon name="console" strokeWidth={2.5} />
            Console VNC
          </button>
          
          <ActionButtons 
            isRunning={isRunning} 
            onStart={() => startVM(vm.id)} 
            onStop={() => stopVM(vm.id)} 
            onReboot={() => rebootVM(vm.id)} 
            onDelete={() => {
              if (confirm("Supprimer cette VM ?")) {
                deleteVM(vm.id);
                router.push('/dashboard/mes-vms');
              }
            }}
          />
        </div>
      </div>

      {/* 2. STATS GRID */}
      <div className="vm-stats-grid">
        <StatCard label="vCPU" value={`${vm.vcpu} Cores`} usage={vm.cpu_usage} icon="cpu" />
        <StatCard label="RAM" value={`${vm.ram_gb} Go`} usage={vm.ram_usage} icon="ram" />
        <StatCard label="Stockage" value={`${vm.storage_gb} Go`} icon="disk" />
        <StatCard label="IP" value={vm.ip_address || 'Allocation...'} icon="network" />
      </div>

      {/* 3. DETAILS & SSH */}
      <div className="details-section">
        <div className="details-card">
          <div className="details-card-header">
            <Icon name="info" size={18} />
            Paramètres système
          </div>
          <div className="details-card-body">
            <EditableRow label="Nom de la machine" value={vm.name} field="name" editingField={editingField} editValue={editValue} onEdit={handleEdit} onSave={saveEdit} onChange={setEditValue} />
            <div className="detail-row"><span className="detail-label">OS</span><span className="detail-value">Ubuntu 22.04 LTS</span></div>
            <EditableRow label="vCPU" value={`${vm.vcpu} Cores`} field="cpu" editingField={editingField} editValue={editValue} onEdit={handleEdit} onSave={saveEdit} onChange={setEditValue} type="number" />
            <EditableRow label="RAM" value={`${vm.ram_gb} Go`} field="ram" editingField={editingField} editValue={editValue} onEdit={handleEdit} onSave={saveEdit} onChange={setEditValue} type="number" />
            <div className="detail-row"><span className="detail-label">Créée le</span><span className="detail-value">{new Date(vm.lease_start).toLocaleDateString()}</span></div>
          </div>
        </div>

        <SSHCard ip={vm.ip_address} hasKey={!!vm.ssh_public_key} onDownload={downloadKey} />
      </div>
    </div>
  );
}

// SUB-COMPONENTS
function VMNotFound({ vmid, onBack }: any) {
  return (
    <div className="page active" style={{ padding: '40px' }}>
      <div className="vm-panel" style={{ padding: '40px', textAlign: 'center' }}>
        <h2 style={{ color: '#fff' }}>VM introuvable</h2>
        <p style={{ color: 'var(--g1-muted)', margin: '12px 0 24px' }}>L'identifiant {vmid} est incorrect.</p>
        <button className="btn-accent" onClick={onBack}>Retour à la liste</button>
      </div>
    </div>
  );
}

function StatCard({ label, value, usage, icon }: any) {
  return (
    <div className="stat-card">
      <div className="stat-card-label"><Icon name={icon} size={14} /> {label}</div>
      <div className="stat-card-value">{value}</div>
      {usage !== undefined && (
        <>
          <div className="stat-card-footer">Usage: {usage}%</div>
          <div className="usage-bar">
            <div className="usage-fill" style={{ width: `${usage}%`, background: usage > 80 ? 'var(--g1-err)' : 'var(--g1-accent2)' }}></div>
          </div>
        </>
      )}
    </div>
  );
}

function EditableRow({ label, value, field, editingField, editValue, onEdit, onSave, onChange, type = "text" }: any) {
  const isEditing = editingField === field;
  return (
    <div className="detail-row">
      <div className="detail-label">{label}</div>
      <div className="detail-value">
        {isEditing ? (
          <input 
            className="pm-input" 
            type={type} 
            style={{ padding: '4px 8px', width: '120px', height: '28px' }} 
            value={editValue} 
            onChange={e => onChange(e.target.value)} 
            onBlur={onSave} 
            autoFocus 
          />
        ) : (
          <span onClick={() => onEdit(field, value)} style={{ cursor: 'pointer', borderBottom: '1px dashed rgba(255,255,255,0.2)' }}>{value}</span>
        )}
      </div>
    </div>
  );
}

function SSHCard({ ip, hasKey, onDownload }: any) {
  return (
    <div className="details-card" style={{ borderTopColor: 'var(--g1-accent2)' }}>
      <div className="details-card-header">
        <Icon name="lock" size={18} />
        Accès SSH
      </div>
      <div className="pm-body">
        <p style={{ fontSize: '13px', color: 'var(--g1-muted)', marginBottom: '12px' }}>Connectez-vous via terminal :</p>
        <code style={{ display: 'block', background: '#030610', padding: '12px', borderRadius: '8px', border: '1px solid var(--g1-border)', color: 'var(--g1-accent)', fontSize: '12px' }}>
          ssh ubuntu@{ip || 'IP'}
        </code>
        {hasKey ? (
          <button className="btn-primary" style={{ width: '100%', marginTop: '16px' }} onClick={onDownload}>
            <Icon name="download" />
            Télécharger la clé (.pub)
          </button>
        ) : (
          <div className="pm-alert pm-alert-warn" style={{ marginTop: '16px' }}>
            <p>Clé déjà téléchargée.</p>
          </div>
        )}
      </div>
    </div>
  );
}

function ActionButtons({ isRunning, onStart, onStop, onReboot, onDelete }: any) {
  return (
    <>
      {isRunning ? (
        <button className="btn-vm btn-vm-stop" onClick={onStop}>
          <Icon name="stop" />Arrêter
        </button>
      ) : (
        <button className="btn-vm btn-vm-start" onClick={onStart}>
          <Icon name="start" />Démarrer
        </button>
      )}
      <button className="btn-vm" onClick={onReboot}>
        <Icon name="reboot" />Reboot
      </button>
      <button className="btn-vm" style={{ color: 'var(--g1-err)' }} onClick={onDelete}>
        <Icon name="delete" />Delete
      </button>
    </>
  );
}
