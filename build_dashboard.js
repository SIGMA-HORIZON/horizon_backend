const fs = require('fs');
const html = fs.readFileSync('/Users/computer-care/horizon_frontend/public/example.html', 'utf8');

// 1. Extract CSS
let cssMatch = html.match(/<style>([\s\S]*?)<\/style>/);
let css = cssMatch ? cssMatch[1] : '';
// Replace variables with our theme mappings
css = css.replace(/var\(--g1-dark\)/g, 'var(--bg-deep)');
css = css.replace(/var\(--g1-surface\)/g, 'var(--bg-deep)');
css = css.replace(/var\(--g1-card\)/g, 'var(--bg-card)');
css = css.replace(/var\(--g1-border\)/g, 'var(--border)');
css = css.replace(/var\(--g1-text\)/g, 'var(--text-white)');
css = css.replace(/var\(--g1-muted\)/g, 'var(--text-muted)');
css = css.replace(/var\(--g1-accent\)/g, 'var(--cyan)');
css = css.replace(/var\(--g1-accent2\)/g, 'var(--blue-mid)');
css = css.replace(/var\(--g1-tag\)/g, 'var(--blue-glow)');
css = css.replace(/var\(--g1-tag-text\)/g, 'var(--cyan)');
css = css.replace(/var\(--g1-nav\)/g, 'var(--bg-hover)');

fs.mkdirSync('/Users/computer-care/horizon_frontend/app/dashboard', { recursive: true });
fs.writeFileSync('/Users/computer-care/horizon_frontend/app/dashboard/dashboard.css', css);

// Helper to clean JSX
function toJSX(str) {
  let jsx = str
    .replace(/class=/g, 'className=')
    .replace(/onclick="[^"]*"/g, '')
    .replace(/<br>/g, '<br/>')
    .replace(/<!--[\s\S]*?-->/g, '')
    .replace(/<input([^>]*?)>/g, (m, g) => (m.endsWith('/>') ? m : `<input${g}/>`))
    .replace(/<img(.*?)>/g, (m, g) => (m.endsWith('/>') ? m : `<img${g}/>`));

  // Remove generic inline styles for simplicity except those easily parsable or just remove them
  // A simple regex to convert style="width:64%" to style={{width: '64%'}} safely
  jsx = jsx.replace(/style="([^"]*)"/g, (match, p1) => {
    const parts = p1.split(';').filter(Boolean);
    const rules = parts.map(p => {
      const sp = p.split(':');
      if(sp.length!==2) return '';
      let key = sp[0].trim().replace(/-([a-z])/g, g => g[1].toUpperCase());
      let val = sp[1].trim();
      return `${key}: '${val}'`;
    }).filter(Boolean);
    return `style={{ ${rules.join(', ')} }}`;
  });
  return jsx;
}

// 2. Extract Sidebar & Topbar for Layout
const sidebarMatch = html.match(/<div class="sidebar">([\s\S]*?)<\/div>\s*<!-- MAIN -->/);
let sidebar = sidebarMatch ? sidebarMatch[1] : '';

const topbarMatch = html.match(/<div class="topbar">([\s\S]*?)<\/div>\s*<div class="content">/);
let topbar = topbarMatch ? topbarMatch[1] : '';

// Convert navItems to Links
sidebar = sidebar
  .replace(/<div class="nav-item(.*?)"(.*?)>\s*<svg([\s\S]*?)<\/svg>\s*Dashboard\s*<\/div>/, '<Link href="/dashboard" className="nav-item$1"><svg$3</svg>Dashboard</Link>')
  .replace(/<div class="nav-item(.*?)"(.*?)>\s*<svg([\s\S]*?)<\/svg>\s*Mes VMs([\s\S]*?)<\/div>/, '<Link href="/dashboard/mes-vms" className="nav-item$1"><svg$3</svg>Mes VMs$4</Link>')
  .replace(/<div class="nav-item(.*?)"(.*?)>\s*<svg([\s\S]*?)<\/svg>\s*Réservations\s*<\/div>/, '<Link href="/dashboard/reservations" className="nav-item$1"><svg$3</svg>Réservations</Link>')
  .replace(/<div class="nav-item(.*?)"(.*?)>\s*<svg([\s\S]*?)<\/svg>\s*Clés SSH\s*<\/div>/, '<Link href="/dashboard/ssh" className="nav-item$1"><svg$3</svg>Clés SSH</Link>')
  .replace(/<div class="nav-item(.*?)"(.*?)>\s*<svg([\s\S]*?)<\/svg>\s*Mon Profil\s*<\/div>/, '<Link href="/dashboard/profil" className="nav-item$1"><svg$3</svg>Mon Profil</Link>');

// Wrap in Layout
const layoutJSX = `
"use client";
import React from 'react';
import Link from 'next/link';
import './dashboard.css';
import '../home.css';

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="home-theme">
      <div className="shell">
        <div className="sidebar">
          ${toJSX(sidebar)}
        </div>
        <div className="main">
          <div className="topbar">
            ${toJSX(topbar)}
          </div>
          <div className="content">
            {children}
          </div>
        </div>
      </div>
    </div>
  );
}
`;
fs.writeFileSync('/Users/computer-care/horizon_frontend/app/dashboard/layout.tsx', layoutJSX);

// 3. Extract Pages
const dashboardPage = html.match(/<!-- PAGE: DASHBOARD -->([\s\S]*?)<!-- PAGE: MES VMs -->/)[1];
const mesVmsPage = html.match(/<!-- PAGE: MES VMs -->([\s\S]*?)<!-- PAGE: RÉSERVATIONS -->/)[1];
const reservationsPage = html.match(/<!-- PAGE: RÉSERVATIONS -->([\s\S]*?)<!-- PAGE: CLÉS SSH -->/)[1];
const sshPage = html.match(/<!-- PAGE: CLÉS SSH -->([\s\S]*?)<!-- PAGE: MON PROFIL -->/)[1];
const profilPage = html.match(/<!-- PAGE: MON PROFIL -->([\s\S]*?)<\/div>\s*<\/div>\s*<\/div>\s*<!-- LOGOUT/)[1];

fs.writeFileSync('/Users/computer-care/horizon_frontend/app/dashboard/page.tsx', `
export default function DashboardHome() {
  return (
    <div className="page active">
      ${toJSX(dashboardPage)}
    </div>
  )
}
`);

fs.mkdirSync('/Users/computer-care/horizon_frontend/app/dashboard/mes-vms', { recursive: true });

// Modification requested by user: Add "Créer une VM" as subtitle below "Mes VMs"
// The Mes VMs page has `<button class="btn-accent" onclick="showCreateVM()">+ Créer une VM</button>`
// User meant: "ajouter un bouton creer une vms en sous titre en bas de 'mes vms'" -> add it explicitly if not present, but let's make it clearer.
// "pour chaque vms dédie une page entière pour voir les détails" -> make table rows click to /dashboard/mes-vms/[vmid]
let cleanedMesVms = toJSX(mesVmsPage);
cleanedMesVms = cleanedMesVms.replace(/<tr\s*style=\{\{\s*cursor:\s*'pointer'\s*\}\}\s*>/g, '<tr style={{ cursor: "pointer" }}>');
// Let's replace the onClick for TR with Link or onClick next/router
// Simply replacing <tr> logic. The <tr onClick="..."> needs router logic.
fs.writeFileSync('/Users/computer-care/horizon_frontend/app/dashboard/mes-vms/page.tsx', `
"use client";
import { useRouter } from 'next/navigation';

export default function MesVMs() {
  const router = useRouter();

  return (
    <div className="page active">
      <div style={{ paddingBottom: '20px' }}>
         <h1 style={{ fontSize: '24px', fontWeight: 'bold' }}>Mes VMs</h1>
         <button className="btn-accent" style={{ marginTop: '5px' }}>+ Créer une VM</button>
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
              <th>Nœud</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr onClick={() => router.push('/dashboard/mes-vms/vm-ml-01')} style={{ cursor: 'pointer' }}>
              <td style={{ padding: '10px 16px' }}><div style={{ fontWeight: 600, fontSize: '12px' }}>vm-ml-ornella-01</div><div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>VMID 101</div></td>
              <td><span className="badge badge-on">● Running</span></td>
              <td><span className="badge badge-blue">Ubuntu 22.04</span></td>
              <td><div style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '12px' }}>64%<div className="mini-bar"><div className="mini-fill mini-fill-warn" style={{ width: '64%' }}></div></div></div></td>
              <td style={{ fontSize: '12px' }}>9.2 / 16 Go</td>
              <td style={{ fontSize: '11px', fontFamily: 'monospace', color: 'var(--text-muted)' }}>10.0.1.1</td>
              <td><span className="badge badge-off">node-01</span></td>
              <td>
                <div style={{ display: 'flex', gap: '4px' }}>
                  <button className="btn-vm btn-vm-console" style={{ fontSize: '10px', padding: '3px 8px' }}>Console</button>
                  <button className="btn-vm btn-vm-stop" style={{ fontSize: '10px', padding: '3px 8px' }}>Stop</button>
                </div>
              </td>
            </tr>
            <tr onClick={() => router.push('/dashboard/mes-vms/vm-dev-02')} style={{ cursor: 'pointer' }}>
              <td style={{ padding: '10px 16px' }}><div style={{ fontWeight: 600, fontSize: '12px' }}>vm-dev-ornella-02</div><div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>VMID 102</div></td>
              <td><span className="badge badge-on">● Running</span></td>
              <td><span className="badge badge-blue">Debian 12</span></td>
              <td><div style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '12px' }}>22%<div className="mini-bar"><div className="mini-fill" style={{ width: '22%' }}></div></div></div></td>
              <td style={{ fontSize: '12px' }}>2.7 / 8 Go</td>
              <td style={{ fontSize: '11px', fontFamily: 'monospace', color: 'var(--text-muted)' }}>10.0.1.2</td>
              <td><span className="badge badge-off">node-02</span></td>
              <td>
                <div style={{ display: 'flex', gap: '4px' }}>
                  <button className="btn-vm btn-vm-console" style={{ fontSize: '10px', padding: '3px 8px' }}>Console</button>
                  <button className="btn-vm btn-vm-stop" style={{ fontSize: '10px', padding: '3px 8px' }}>Stop</button>
                </div>
              </td>
            </tr>
            <tr onClick={() => router.push('/dashboard/mes-vms/vm-gpu-03')} style={{ cursor: 'pointer' }}>
              <td style={{ padding: '10px 16px' }}><div style={{ fontWeight: 600, fontSize: '12px' }}>vm-gpu-ornella-03</div><div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>VMID 103</div></td>
              <td><span className="badge badge-warn">⚠ High CPU</span></td>
              <td><span className="badge badge-blue">Ubuntu 22.04</span></td>
              <td><div style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '12px' }}>91%<div className="mini-bar"><div className="mini-fill mini-fill-err" style={{ width: '91%' }}></div></div></div></td>
              <td style={{ fontSize: '12px' }}>51.2 / 64 Go</td>
              <td style={{ fontSize: '11px', fontFamily: 'monospace', color: 'var(--text-muted)' }}>10.0.1.3</td>
              <td><span className="badge badge-off">node-03</span></td>
              <td>
                <div style={{ display: 'flex', gap: '4px' }}>
                  <button className="btn-vm btn-vm-console" style={{ fontSize: '10px', padding: '3px 8px' }}>Console</button>
                  <button className="btn-vm btn-vm-stop" style={{ fontSize: '10px', padding: '3px 8px' }}>Stop</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  )
}
`);

// Create individual VM details page
fs.mkdirSync('/Users/computer-care/horizon_frontend/app/dashboard/mes-vms/[vmid]', { recursive: true });
fs.writeFileSync('/Users/computer-care/horizon_frontend/app/dashboard/mes-vms/[vmid]/page.tsx', `
"use client";
import { useParams } from 'next/navigation';

export default function VMDetails() {
  const params = useParams();
  const vmid = params.vmid;

  return (
    <div className="page active" style={{ padding: '20px' }}>
      <h2 style={{ fontSize: '24px', fontWeight: 'bold', marginBottom: '20px' }}>Détails de la VM: {vmid}</h2>
      
      <div className="vm-panel" id="myvms-vm-panel">
        <div className="vm-panel-hdr">
          <div>
            <div className="vm-panel-title">{vmid}</div>
            <div className="vm-panel-meta">VMID XXX · node-01 · Ubuntu 22.04 · <span style={{ color: 'var(--g1-on)', fontWeight: 600 }}>Running</span></div>
          </div>
          <div className="vm-actions">
            <button className="btn-vm btn-vm-console">
              <svg viewBox="0 0 24 24"><rect x="2" y="3" width="20" height="14" rx="2"/><path d="M8 21h8M12 17v4"/></svg>Console
            </button>
            <button className="btn-vm btn-vm-stop">
              <svg viewBox="0 0 24 24"><rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/></svg>Stop
            </button>
            <button className="btn-vm">
              <svg viewBox="0 0 24 24"><path d="M1 4v6h6M23 20v-6h-6"/><path d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10M23 14l-4.64 4.36A9 9 0 0 1 3.51 15"/></svg>Redémarrer
            </button>
          </div>
        </div>
        <div className="vm-tabs">
          <div className="vm-tab active">Summary</div>
          <div className="vm-tab">Console</div>
          <div className="vm-tab">Hardware</div>
          <div className="vm-tab">Cloud-init</div>
          <div className="vm-tab">Options</div>
          <div className="vm-tab">Tasks history</div>
          <div className="vm-tab">Monitor</div>
          <div className="vm-tab">Backup</div>
          <div className="vm-tab">Snapshots</div>
          <div className="vm-tab">Firewall</div>
          <div className="vm-tab">Permissions</div>
        </div>
        <div className="vm-tab-body">
          <p style={{ padding: '20px' }}>Les onglets de gestion de la machine {vmid} se trouvent ici.</p>
        </div>
      </div>
    </div>
  )
}
`);

fs.mkdirSync('/Users/computer-care/horizon_frontend/app/dashboard/reservations', { recursive: true });
fs.writeFileSync('/Users/computer-care/horizon_frontend/app/dashboard/reservations/page.tsx', `
export default function Reservations() {
  return (
    <div className="page active">
      ${toJSX(reservationsPage)}
    </div>
  )
}
`);

fs.mkdirSync('/Users/computer-care/horizon_frontend/app/dashboard/ssh', { recursive: true });
fs.writeFileSync('/Users/computer-care/horizon_frontend/app/dashboard/ssh/page.tsx', `
export default function SshKeys() {
  return (
    <div className="page active">
      ${toJSX(sshPage)}
    </div>
  )
}
`);

fs.mkdirSync('/Users/computer-care/horizon_frontend/app/dashboard/profil', { recursive: true });
fs.writeFileSync('/Users/computer-care/horizon_frontend/app/dashboard/profil/page.tsx', `
export default function Profil() {
  return (
    <div className="page active">
      ${toJSX(profilPage)}
    </div>
  )
}
`);

console.log("Dashboard built successfully.");
