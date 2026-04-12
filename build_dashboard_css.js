const fs = require('fs');

const css = `
* { box-sizing:border-box; margin:0; padding:0; font-family:'DM Sans', 'Inter', system-ui, sans-serif; }
.dashboard-theme {
  --g1-dark: #0A1128;
  --g1-nav: #1B2E44;
  --g1-accent: #2563EB;
  --g1-accent2: #3B82F6;
  --g1-surface: #F8FAFC;
  --g1-border: #E2E8F0;
  --g1-text: #0F172A;
  --g1-muted: #64748B;
  --g1-on: #22C55E;
  --g1-warn: #F59E0B;
  --g1-err: #EF4444;
  --g1-off: #94A3B8;
  --g1-card: #FFFFFF;
  --g1-tag: #EFF6FF;
  --g1-tag-text: #1D4ED8;
  
  background: var(--g1-surface);
  color: var(--g1-text);
  min-height: 100vh;
}

.dashboard-theme .shell { display:flex; height:100vh; min-height:700px; }

/* SIDEBAR */
.sidebar { width:260px; min-width:260px; background:var(--g1-dark); display:flex; flex-direction:column; transition: width 0.2s; }
.logo-wrap { padding:24px 20px 20px; border-bottom:1px solid rgba(255,255,255,.08); }
.logo-mark { display:flex; align-items:center; gap:12px; }
.logo-box { width:32px; height:32px; background:linear-gradient(135deg, var(--g1-accent), var(--g1-accent2)); border-radius:8px; display:flex; align-items:center; justify-content:center; box-shadow: 0 4px 12px rgba(37,99,235,.4); }
.logo-box svg { width:18px; height:18px; stroke:#fff; fill:none; stroke-width:2.5; }
.logo-name { font-size:18px; font-weight:700; color:#fff; letter-spacing:.3px; }
.logo-sub { font-size:11px; color:rgba(255,255,255,.45); margin-top:2px; letter-spacing:.8px; }
.nav-wrap { flex:1; overflow-y:auto; padding:16px 0; }
.nav-group { margin-bottom:12px; }
.nav-group-label { font-size:11px; font-weight:600; color:rgba(255,255,255,.3); letter-spacing:1.4px; padding:12px 20px 6px; text-transform:uppercase; }
.nav-item { display:flex; align-items:center; gap:12px; padding:12px 20px; cursor:pointer; font-size:14px; color:rgba(255,255,255,.6); border-left:3px solid transparent; transition:background .2s, color .2s; text-decoration:none; }
.nav-item:hover { background:rgba(255,255,255,.08); color:rgba(255,255,255,.95); }
.nav-item.active { background:rgba(37,99,235,.18); border-left-color:var(--g1-accent2); color:#fff; font-weight:600; }
.nav-item svg { width:18px; height:18px; stroke:currentColor; fill:none; stroke-width:2; flex-shrink:0; }
.nav-vm-list { padding:4px 0 4px 44px; }
.vm-tree-item { display:flex; align-items:center; gap:8px; padding:8px 16px 8px 0; cursor:pointer; font-size:13px; color:rgba(255,255,255,.5); transition:color .2s; }
.vm-tree-item:hover { color:rgba(255,255,255,.9); }
.vm-dot { width:8px; height:8px; border-radius:50%; flex-shrink:0; }
.vm-dot.on { background:var(--g1-on); box-shadow: 0 0 8px var(--g1-on); }
.vm-dot.off { background:var(--g1-off); }
.vm-dot.warn { background:var(--g1-warn); box-shadow: 0 0 8px var(--g1-warn); }

.sidebar-footer { padding:0; border-top:1px solid rgba(255,255,255,.08); background: rgba(0,0,0,0.1); }
.user-row { display:flex; align-items:center; gap:12px; padding:16px 20px; cursor:pointer; transition:background .2s; border-bottom:1px solid rgba(255,255,255,.04); }
.user-row:hover { background:rgba(255,255,255,.06); }
.user-av { width:36px; height:36px; border-radius:50%; background:linear-gradient(135deg,var(--g1-accent),#3B82F6); display:flex; align-items:center; justify-content:center; font-size:13px; font-weight:700; color:#fff; flex-shrink:0; box-shadow:0 0 0 2px rgba(59,130,246,.3); }
.user-name { font-size:14px; color:#fff; font-weight:600; }
.user-role { font-size:11px; color:rgba(255,255,255,.4); margin-top:2px; }
.user-row-chevron { margin-left:auto; color:rgba(255,255,255,.2); }
.user-row-chevron svg { width:16px; height:16px; stroke:currentColor; fill:none; stroke-width:2; }

.logout-btn { display:flex; align-items:center; gap:10px; width:100%; padding:16px 20px; border:none; background:transparent; color:rgba(255,255,255,.4); font-size:14px; cursor:pointer; transition:background .2s, color .2s; text-align:left; font-family: inherit; }
.logout-btn:hover { background:rgba(239,68,68,.15); color:#FCA5A5; }
.logout-btn svg { width:16px; height:16px; stroke:currentColor; fill:none; stroke-width:2; flex-shrink:0; }

/* TOPBAR */
.topbar { background:var(--g1-card); border-bottom:1px solid var(--g1-border); padding:0 32px; height:64px; display:flex; align-items:center; justify-content:space-between; flex-shrink:0; }
.search-box { display:flex; align-items:center; gap:10px; background:var(--g1-surface); border:1px solid var(--g1-border); border-radius:8px; padding:10px 16px; font-size:14px; color:var(--g1-text); min-width:300px; transition: border-color 0.2s, box-shadow 0.2s; }
.search-box:focus-within { border-color: var(--g1-accent); box-shadow: 0 0 0 2px rgba(37,99,235,.15); }
.search-box svg { width:16px; height:16px; stroke:var(--g1-muted); fill:none; stroke-width:2; }
.topbar-right { display:flex; align-items:center; gap:12px; }
.status-pill { display:flex; align-items:center; gap:6px; font-size:13px; background:#F0FDF4; color:#166534; border:1px solid #BBF7D0; padding:6px 14px; border-radius:20px; font-weight:600; }
.status-dot { width:8px; height:8px; border-radius:50%; background:#22C55E; box-shadow: 0 0 6px #22C55E; }

/* BUTTONS */
.btn-accent { background:var(--g1-accent); color:#fff; border:none; padding:10px 18px; border-radius:8px; font-size:14px; font-weight:600; cursor:pointer; transition: transform 0.2s, background 0.2s, box-shadow 0.2s; font-family: inherit; }
.btn-accent:hover { background:var(--g1-accent2); transform: translateY(-1px); box-shadow: 0 4px 12px rgba(37,99,235,.25); }
.btn-ghost { background:var(--g1-card); color:var(--g1-text); border:1px solid var(--g1-border); padding:10px 18px; border-radius:8px; font-size:14px; cursor:pointer; transition: all 0.2s; font-family: inherit; font-weight:500; }
.btn-ghost:hover { background:var(--g1-surface); border-color:#CBD5E1; transform: translateY(-1px); box-shadow: 0 2px 6px rgba(0,0,0,.05); }

/* MAIN CONTENT */
.main { flex:1; display:flex; flex-direction:column; overflow:hidden; }
.content { flex:1; overflow-y:auto; padding:32px 40px; background:var(--g1-surface); }
.page { display:none; animation: fadeIn 0.3s ease; }
.page.active { display:block; }
@keyframes fadeIn { from{opacity:0; transform:translateY(10px)} to{opacity:1; transform:translateY(0)} }

/* WELCOME BANNER */
.welcome { background:var(--g1-card); border:1px solid var(--g1-border); border-radius:12px; padding:32px 36px; margin-bottom:24px; display:flex; align-items:center; justify-content:space-between; box-shadow: 0 4px 6px rgba(0,0,0,.02); }
.welcome-left h2 { font-size:24px; font-weight:700; color:var(--g1-text); margin-bottom:6px; letter-spacing:-0.5px; }
.welcome-left p { font-size:14px; color:var(--g1-muted); }
.welcome-right { display:flex; gap:12px; }

/* VM STATUS CARDS */
.vm-status-row { display:grid; grid-template-columns:repeat(3, minmax(0,1fr)); gap:20px; margin-bottom:24px; }
.vm-status-card { background:var(--g1-card); border:1px solid var(--g1-border); border-radius:12px; padding:20px 24px; cursor:pointer; transition: all 0.2s ease; box-shadow: 0 2px 4px rgba(0,0,0,.02); }
.vm-status-card:hover { transform: translateY(-3px); border-color:var(--g1-accent2); box-shadow: 0 8px 16px rgba(37,99,235,.08); }
.vm-status-card.selected { border-color:var(--g1-accent); border-width:2px; box-shadow: 0 6px 12px rgba(37,99,235,.15); padding: 19px 23px; }
.vsc-top { display:flex; align-items:center; justify-content:space-between; margin-bottom:12px; }
.vsc-name { font-size:16px; font-weight:700; color:var(--g1-text); }
.vsc-id { font-size:12px; color:var(--g1-muted); margin-top:4px; }
.vsc-meta { font-size:13px; color:var(--g1-muted); margin-top:10px; }

/* BADGES */
.badge { display:inline-flex; align-items:center; gap:6px; font-size:12px; font-weight:600; padding:4px 10px; border-radius:12px; }
.badge-on { background:#F0FDF4; color:#166534; border:1px solid #BBF7D0; }
.badge-off { background:#F8FAFC; color:#64748B; border:1px solid #E2E8F0; }
.badge-warn { background:#FFFBEB; color:#92400E; border:1px solid #FDE68A; }
.badge-blue { background:var(--g1-tag); color:var(--g1-tag-text); border:1px solid #BFDBFE; }
.badge-err { background:#FEF2F2; color:#991B1B; border:1px solid #FECACA; }

/* VM PANEL / TABS */
.vm-panel { background:var(--g1-card); border:1px solid var(--g1-border); border-radius:12px; overflow:hidden; box-shadow: 0 4px 12px rgba(0,0,0,.03); }
.vm-panel-hdr { padding:20px 24px; border-bottom:1px solid var(--g1-border); display:flex; align-items:center; justify-content:space-between; }
.vm-panel-title { font-size:18px; font-weight:700; color:var(--g1-text); }
.vm-panel-meta { font-size:13px; color:var(--g1-muted); margin-top:4px; }
.vm-actions { display:flex; gap:8px; }
.btn-vm { border:1px solid var(--g1-border); background:transparent; color:var(--g1-text); font-size:13px; padding:8px 14px; border-radius:6px; cursor:pointer; font-weight:600; display:flex; align-items:center; gap:6px; transition: all 0.2s; font-family: inherit;}
.btn-vm svg { width:14px; height:14px; stroke:currentColor; fill:none; stroke-width:2; }
.btn-vm:hover { transform: translateY(-1px); box-shadow: 0 2px 4px rgba(0,0,0,.05); }
.btn-vm-start { border-color:#BBF7D0; color:#166534; background:#F0FDF4; }
.btn-vm-start:hover { background: #DCFCE7; border-color:#86EFAC; }
.btn-vm-stop { border-color:#FECACA; color:#991B1B; background:#FEF2F2; }
.btn-vm-stop:hover { background: #FEE2E2; border-color:#F87171; }
.btn-vm-console { border-color:#BFDBFE; color:#1D4ED8; background:var(--g1-tag); }
.btn-vm-console:hover { background: #DBEAFE; border-color:#93C5FD; }

.vm-tabs { display:flex; gap:0; border-bottom:1px solid var(--g1-border); overflow-x:auto; padding:0 24px; scrollbar-width:none; background:#F8FAFC; }
.vm-tabs::-webkit-scrollbar { display:none; }
.vm-tab { padding:14px 18px; font-size:14px; font-weight:500; color:var(--g1-muted); cursor:pointer; border-bottom:2px solid transparent; white-space:nowrap; transition:all .2s; }
.vm-tab:hover { color:var(--g1-text); background: rgba(0,0,0,.02); }
.vm-tab.active { color:var(--g1-accent); border-bottom-color:var(--g1-accent); font-weight:600; background: var(--g1-card); }
.vm-tab-body { padding:24px; min-height:300px; }

/* TABLES */
table { width:100%; border-collapse:collapse; font-size:14px; }
thead th { text-align:left; padding:12px 20px; color:var(--g1-muted); font-weight:600; border-bottom:2px solid var(--g1-border); font-size:12px; text-transform:uppercase; letter-spacing:.5px; }
tbody tr { border-bottom:1px solid #F1F5F9; transition: background 0.15s; }
tbody tr:hover { background:#F8FAFD; }
tbody td { padding:14px 20px; vertical-align:middle; }

/* MINI BARS */
.mini-bar { height:6px; background:#E2E8F0; border-radius:3px; overflow:hidden; width:80px; display:inline-block; vertical-align:middle; margin-left: 8px; }
.mini-fill { height:100%; border-radius:3px; background:var(--g1-accent); }
.mini-fill-warn { background:var(--g1-warn); }
.mini-fill-err { background:var(--g1-err); }

/* PROFILE PAGE */
.profile-header { background:linear-gradient(135deg, #1E3A5F 0%, #0F2241 100%); border:1px solid var(--g1-border); border-radius:12px; padding:32px 40px; margin-bottom:24px; display:flex; align-items:center; gap:24px; position:relative; overflow:hidden; box-shadow: 0 8px 16px rgba(0,0,0,.05); }
.profile-av-lg { width:72px; height:72px; border-radius:50%; background:linear-gradient(135deg,var(--g1-accent),#3B82F6); display:flex; align-items:center; justify-content:center; font-size:28px; font-weight:700; color:#fff; flex-shrink:0; box-shadow:0 0 0 4px rgba(59,130,246,.35),0 0 24px rgba(37,99,235,.4); }
.profile-hdr-info h2 { font-size:24px; font-weight:700; color:#fff; margin-bottom:4px; }
.profile-hdr-info p { font-size:14px; color:rgba(255,255,255,.65); }
.profile-hdr-badge { display:inline-flex; align-items:center; gap:6px; background:rgba(37,99,235,.3); border:1px solid rgba(59,130,246,.4); color:#93C5FD; font-size:12px; font-weight:600; padding:4px 14px; border-radius:20px; margin-top:10px; letter-spacing:.5px; }
.profile-grid { display:grid; grid-template-columns:1fr 1fr; gap:20px; margin-bottom:24px; }
.profile-card { background:var(--g1-card); border:1px solid var(--g1-border); border-radius:12px; overflow:hidden; box-shadow: 0 2px 6px rgba(0,0,0,.02); transition: transform 0.2s; }
.profile-card:hover { transform: translateY(-2px); box-shadow: 0 6px 16px rgba(0,0,0,.04); }
.profile-card-hdr { padding:16px 20px; border-bottom:1px solid var(--g1-border); display:flex; align-items:center; gap:10px; font-size:15px; font-weight:600; color:var(--g1-text); background:#F8FAFC; }
.profile-card-hdr svg { width:18px; height:18px; stroke:var(--g1-accent); fill:none; stroke-width:2; }
.profile-field { padding:12px 20px; border-bottom:1px solid #F8FAFD; display:flex; flex-direction:column; gap:4px; }
.profile-field:last-child { border-bottom:none; }
.profile-field label { font-size:11px; font-weight:600; color:var(--g1-muted); text-transform:uppercase; letter-spacing:.6px; }
.profile-field span { font-size:14px; color:var(--g1-text); font-weight:500; }

.fw-rule { display:grid; grid-template-columns:60px 80px 1fr 1fr 70px 60px; gap:12px; padding:10px 0; border-bottom:1px solid #F1F5F9; font-size:13px; align-items:center; }
.fw-hdr { font-weight:600; color:var(--g1-muted); font-size:11px; text-transform:uppercase; letter-spacing:.5px; }

.task-row { display:flex; align-items:flex-start; gap:12px; padding:10px 0; border-bottom:1px solid #F1F5F9; font-size:13px; }
.task-dot { width:10px; height:10px; border-radius:50%; margin-top:3px; flex-shrink:0; }
.task-ok { background:var(--g1-on); } .task-warn { background:var(--g1-warn); } .task-err { background:var(--g1-err); }
.task-desc { color:var(--g1-text); font-weight:500; }
.task-time { color:var(--g1-muted); font-size:12px; margin-top:2px; }

`;

fs.writeFileSync('/Users/computer-care/horizon_frontend/app/dashboard/dashboard.css', css);
console.log('CSS Rebuilt manually to restore light theme inside dashboard');
