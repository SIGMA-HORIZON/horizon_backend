"use client";
import React from 'react';
import './home.css';
import Header from './components/Header';
import Footer from './components/Footer';

export default function Home() {
  return (
    <div className="home-theme">
      <link rel="preconnect" href="https://fonts.googleapis.com"/>
      <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous"/>
      <link href="https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;500;600;700&family=DM+Sans:opsz,wght@9..40,300;9..40,400;9..40,500;9..40,600&display=swap" rel="stylesheet"/>
      
      <Header />

      <section className="hero" style={{ 
        backgroundImage: 'linear-gradient(rgba(0,0,0,0.7), rgba(0,0,0,0.7)), url("/hero-bg.jpg")',
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        padding: '160px 20px 120px'
      }}>
        <div className="scan-line" style={{ top: '65%' }}></div>

        <div className="hero-inner">
          <div className="hero-badge">
            <span className="badge-dot"></span>
            Cloud Horizon · ENSPY · Opérationnel
          </div>

          <h1>
            La puissance du Cloud<br/>
            <span className="accent">simplifiée</span> pour vous.
          </h1>

          <div className="hero-sub-title">Virtualisation & Infrastructure Cloud</div>

          <p>
            Horizon donne aux étudiants et chercheurs de l'ENSPY un accès autonome
            aux ressources — serveurs virtuels, stockage haute disponibilité, réseaux isolés —
            avec une simplicité déconcertante.
          </p>

          <div className="hero-actions">
            <a href="/demande_compte" className="btn-hero-primary">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><line x1="19" y1="8" x2="19" y2="14"/><line x1="22" y1="11" x2="16" y2="11"/></svg>
              Demander un accès
            </a>
            <a href="#features" className="btn-hero-ghost">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><circle cx="12" cy="16" r=".5" fill="currentColor"/></svg>
              En savoir plus
            </a>
          </div>
        </div>

        <div className="scroll-hint">
          <div className="scroll-mouse"></div>
          Défiler
        </div>
      </section>

      <section className="stats-section">
        <div className="stats-bar">
          <div className="stat-item">
            <div className="stat-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="2" y="3" width="20" height="14" rx="2"/><path d="M8 21h8M12 17v4"/></svg>
            </div>
            <div className="stat-num">12<span>+</span></div>
            <div className="stat-label">Machines virtuelles</div>
          </div>
          <div className="stat-item">
            <div className="stat-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 20V10M12 20V4M6 20v-6"/></svg>
            </div>
            <div className="stat-num">128<span>Go</span></div>
            <div className="stat-label">RAM par nœud</div>
          </div>
          <div className="stat-item">
            <div className="stat-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/></svg>
            </div>
            <div className="stat-num">10<span>To</span></div>
            <div className="stat-label">Stockage Cloud</div>
          </div>
          <div className="stat-item">
            <div className="stat-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
            </div>
            <div className="stat-num">60<span>+</span></div>
            <div className="stat-label">Utilisateurs actifs</div>
          </div>
        </div>
      </section>

      <section className="features-section" id="features" style={{ display: 'flex', flexDirection: 'column', gap: '80px', paddingBottom: '80px' }}>
        <div className="section-header">
          <div className="section-tag">Fonctionnalités</div>
          <h2>Tout ce dont vous avez besoin<br/>pour vos projets Cloud</h2>
          <p>Une plateforme complète pensée pour les besoins académiques : TP, développement, infrastructure de serveurs.</p>
        </div>

        {/* Feature 1: Cloud & VMs */}
        <div className="feature-showcase" style={{ display: 'flex', alignItems: 'center', gap: '40px', flexWrap: 'wrap', background: 'rgba(255,255,255,0.02)', padding: '40px', borderRadius: '24px', border: '1px solid rgba(255,255,255,0.05)' }}>
          <div className="feature-text" style={{ flex: 1, minWidth: '300px' }}>
            <h3 style={{ fontSize: '28px', color: 'white', marginBottom: '16px' }}>Virtualisation instantanée</h3>
            <p style={{ color: 'var(--text-muted)', fontSize: '16px', lineHeight: '1.6', marginBottom: '24px' }}>
              Déployez des serveurs virtuels (Ubuntu, Debian, Fedora, CentOS) en quelques minutes. Accédez nativement via une console web intégrée ou par votre terminal via SSH. Idéal pour vos environnements de développement.
            </p>
            <ul style={{ listStyle: 'none', padding: 0, margin: 0, color: 'var(--text-muted)' }}>
              <li style={{ marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '12px' }}><span style={{ color: 'var(--cyan)' }}>✓</span> Déploiement ultra-rapide</li>
              <li style={{ marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '12px' }}><span style={{ color: 'var(--cyan)' }}>✓</span> Images OS pré-configurées</li>
              <li style={{ display: 'flex', alignItems: 'center', gap: '12px' }}><span style={{ color: 'var(--cyan)' }}>✓</span> Accès réseau isolé</li>
            </ul>
          </div>
          <div className="feature-image" style={{ flex: 1, minWidth: '300px', borderRadius: '16px', overflow: 'hidden', boxShadow: '0 20px 40px rgba(0,0,0,0.4)', border: '1px solid rgba(255,255,255,0.1)' }}>
            <img src="/feature_cloud.png" alt="Cloud Infrastructure" style={{ width: '100%', height: '400px', display: 'block', objectFit: 'cover' }} />
          </div>
        </div>

        {/* Feature 2: High Availability and Distribution */}
        <div className="feature-showcase" style={{ display: 'flex', alignItems: 'center', gap: '40px', flexWrap: 'wrap-reverse', background: 'rgba(255,255,255,0.02)', padding: '40px', borderRadius: '24px', border: '1px solid rgba(255,255,255,0.05)' }}>
          <div className="feature-image" style={{ flex: 1, minWidth: '300px', borderRadius: '16px', overflow: 'hidden', boxShadow: '0 20px 40px rgba(0,0,0,0.4)', border: '1px solid rgba(255,255,255,0.1)' }}>
            <img src="https://images.unsplash.com/photo-1558483301-381676672320?auto=format&fit=crop&w=800&q=80" alt="Server Rack" style={{ width: '100%', height: '400px', display: 'block', objectFit: 'cover' }} />
          </div>
          <div className="feature-text" style={{ flex: 1, minWidth: '300px' }}>
            <h3 style={{ fontSize: '28px', color: 'white', marginBottom: '16px' }}>Évolutivité & Stockage</h3>
            <p style={{ color: 'var(--text-muted)', fontSize: '16px', lineHeight: '1.6', marginBottom: '24px' }}>
              Gérez vos ressources avec une flexibilité totale. Augmentez la capacité de vos serveurs (CPU/RAM) selon vos besoins et profitez d'un stockage distribué (Ceph) garantissant la persistance et la sécurité de vos données critiques.
            </p>
            <ul style={{ listStyle: 'none', padding: 0, margin: 0, color: 'var(--text-muted)' }}>
              <li style={{ marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '12px' }}><span style={{ color: 'var(--cyan)' }}>✓</span> Infrastructure haute performance</li>
              <li style={{ marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '12px' }}><span style={{ color: 'var(--cyan)' }}>✓</span> Stockage persistant redondant</li>
              <li style={{ display: 'flex', alignItems: 'center', gap: '12px' }}><span style={{ color: 'var(--cyan)' }}>✓</span> Snapshots & Sauvegardes</li>
            </ul>
          </div>
        </div>

        {/* Feature 3: Security & Management */}
        <div className="feature-showcase" style={{ display: 'flex', alignItems: 'center', gap: '40px', flexWrap: 'wrap', background: 'rgba(255,255,255,0.02)', padding: '40px', borderRadius: '24px', border: '1px solid rgba(255,255,255,0.05)' }}>
          <div className="feature-text" style={{ flex: 1, minWidth: '300px' }}>
            <h3 style={{ fontSize: '28px', color: 'white', marginBottom: '16px' }}>Sécurité & Pilotage</h3>
            <p style={{ color: 'var(--text-muted)', fontSize: '16px', lineHeight: '1.6', marginBottom: '24px' }}>
              Pilotez vous-même le cycle de vie de vos serveurs (démarrage, arrêt, snapshots) depuis une interface intuitive. Votre accès SSH est sécurisé en toute transparence par l'injection de votre clé au lancement via Cloud-init.
            </p>
            <ul style={{ listStyle: 'none', padding: 0, margin: 0, color: 'var(--text-muted)' }}>
              <li style={{ marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '12px' }}><span style={{ color: 'var(--cyan)' }}>✓</span> Sécurisation SSH automatisée</li>
              <li style={{ marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '12px' }}><span style={{ color: 'var(--cyan)' }}>✓</span> Alertes en direct de consommation</li>
              <li style={{ display: 'flex', alignItems: 'center', gap: '12px' }}><span style={{ color: 'var(--cyan)' }}>✓</span> Suivi complet dans le dashboard</li>
            </ul>
          </div>
          <div className="feature-image" style={{ flex: 1, minWidth: '300px', borderRadius: '16px', overflow: 'hidden', boxShadow: '0 20px 40px rgba(0,0,0,0.4)', border: '1px solid rgba(255,255,255,0.1)' }}>
            <img src="https://images.unsplash.com/photo-1550751827-4bd374c3f58b?auto=format&fit=crop&w=800&q=80" alt="Interface and Security" style={{ width: '100%', height: '400px', display: 'block', objectFit: 'cover' }} />
          </div>
        </div>

      </section>

      <section className="cta-section" id="about">
        <div className="cta-card">
          <div className="cta-glyph">HORIZON</div>

          <div className="hero-badge" style={{ marginBottom: '24px' }}>
            <span className="badge-dot"></span>
            Accès sur demande · ENSPY
          </div>

          <h2>Prêt à rejoindre<br/><span>Horizon</span> ?</h2>
          <p>Soumettez votre demande de compte dès aujourd'hui. Notre équipe traitera votre accès et vous enverra vos identifiants par e-mail institutionnel.</p>

          <div className="cta-actions">
            <a href="/demande_compte" className="btn-hero-primary">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M22 2 11 13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
              Faire une demande
            </a>
            <a href="/connexion" className="btn-hero-ghost">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
              Se connecter
            </a>
          </div>

          <div className="cta-note" style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <span>Projet Horizon · ENSPY 2024–2025</span>
            <a href="/cgu" style={{ color: 'var(--cyan)', textDecoration: 'none', fontSize: '14px' }}>Consulter les conditions d'utilisation</a>
          </div>
        </div>
      </section>

      <Footer />

    </div>
  );
}
