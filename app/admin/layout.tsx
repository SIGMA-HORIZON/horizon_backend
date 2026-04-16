"use client";
import React from 'react';
import Link from 'next/link';
import { useRouter, usePathname } from 'next/navigation';
import '../dashboard/dashboard.css';
import '../home.css';

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();

  return (
    <div className="dashboard-theme">
      <div className="shell">
        <div className="sidebar">

          <div className="logo-wrap">
            <div className="logo-mark">
              <div className="logo-box">
                <svg viewBox="0 0 24 24"><polygon points="12 2 22 8.5 22 15.5 12 22 2 15.5 2 8.5 12 2" /><line x1="12" y1="22" x2="12" y2="15.5" /><polyline points="22 8.5 12 15.5 2 8.5" /></svg>
              </div>
              <div><div className="logo-name">Horizon</div><div className="logo-sub" style={{ color: 'var(--g1-accent2)' }}>Admin Portail</div></div>
            </div>
          </div>

          <div className="nav-wrap">
            <div className="nav-group">
              <div className="nav-group-label">Supervision</div>
              <Link href="/admin" className={`nav-item ${pathname === '/admin' ? 'active' : ''}`}>
                <svg viewBox="0 0 24 24"><rect x="3" y="3" width="7" height="7" rx="1" /><rect x="14" y="3" width="7" height="7" rx="1" /><rect x="3" y="14" width="7" height="7" rx="1" /><rect x="14" y="14" width="7" height="7" rx="1" /></svg>
                Tableau de bord
              </Link>
              <Link href="/admin/noeuds" className={`nav-item ${pathname === '/admin/noeuds' ? 'active' : ''}`}>
                <svg viewBox="0 0 24 24"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" /><polyline points="22 4 12 14.01 9 11.01" /></svg>
                Nœuds cluster
              </Link>
            </div>
            <div className="nav-group">
              <div className="nav-group-label">Gestion</div>
              <Link href="/admin/reservations" className={`nav-item ${pathname === '/admin/reservations' ? 'active' : ''}`}>
                <svg viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="18" rx="2" /><path d="M16 2v4M8 2v4M3 10h18" /></svg>
                Réservations
              </Link>
              <Link href="/admin/bibliotheque" className={`nav-item ${pathname === '/admin/bibliotheque' ? 'active' : ''}`}>
                <svg viewBox="0 0 24 24"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" /><polyline points="3.27 6.96 12 12.01 20.73 6.96" /><line x1="12" y1="22.08" x2="12" y2="12" /></svg>
                Bibliothèque OS
              </Link>
              <Link href="/admin/utilisateurs" className={`nav-item ${pathname === '/admin/utilisateurs' ? 'active' : ''}`}>
                <svg viewBox="0 0 24 24"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" /><circle cx="9" cy="7" r="4" /><path d="M23 21v-2a4 4 0 0 0-3-3.87" /><path d="M16 3.13a4 4 0 0 1 0 7.75" /></svg>
                Utilisateurs
              </Link>
              <Link href="/admin/demandes" className={`nav-item ${pathname === '/admin/demandes' ? 'active' : ''}`}>
                <svg viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><polyline points="14 2 14 8 20 8" /><line x1="16" y1="13" x2="8" y2="13" /><line x1="16" y1="17" x2="8" y2="17" /><polyline points="10 9 9 9 8 9" /></svg>
                Demandes de comptes
              </Link>
            </div>

          </div>

          <div className="sidebar-footer">
            <div className="user-row">
              <div className="user-av" style={{ background: 'linear-gradient(135deg, #10B981, #059669)' }}>AD</div>
              <div style={{ minWidth: '0', flex: '1' }}>
                <div className="user-name">Admin Horizon</div>
                <div className="user-role">Administrateur</div>
              </div>
            </div>
            <button className="logout-btn" onClick={() => router.push('/connexion')}>
              <svg viewBox="0 0 24 24"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" /><polyline points="16 17 21 12 16 7" /><line x1="21" y1="12" x2="9" y2="12" /></svg>
              Déconnexion
            </button>
          </div>

        </div>
        <div className="main">

          <div className="topbar">
            <div className="search-box">
              <svg viewBox="0 0 24 24"><circle cx="11" cy="11" r="8" /><path d="m21 21-4.35-4.35" /></svg>
              Rechercher (Utilisateur, IP, VM)...
            </div>
            <div className="topbar-right">
              <div className="status-pill"><div className="status-dot"></div>Cluster en ligne</div>
              <button className="btn-ghost">Aide</button>
            </div>
          </div>

          <div className="content">
            {children}
          </div>
        </div>
      </div>
    </div>
  );
}
