"use client";
import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

const Header = () => {
  const pathname = usePathname();
  const [activeTab, setActiveTab] = useState('');

  useEffect(() => {
    if (pathname === '/') {
      // For hash links on homepage, maybe 'Accueil' isn't exact, but let's default to it
      setActiveTab('Accueil');
    } else if (pathname === '/cgu') {
      setActiveTab('À propos');
    } else if (pathname === '/demande_compte') {
      setActiveTab('Demande d\'accès');
    } else if (pathname === '/connexion') {
      setActiveTab('Connexion');
    }
  }, [pathname]);

  const navItems = [
    { name: 'Accueil', href: '/' },
    { name: 'Fonctionnalités', href: '/#features' },
    { name: 'Comment ça marche', href: '/#how' }
  ];

  return (
    <nav>
      <div className="nav-brand">
        <div className="nav-logo">
          <svg viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <rect x="2" y="3" width="8" height="8" rx="1"/>
            <rect x="14" y="3" width="8" height="8" rx="1"/>
            <rect x="2" y="13" width="8" height="8" rx="1"/>
            <rect x="14" y="13" width="8" height="8" rx="1"/>
          </svg>
        </div>
        <Link href="/" style={{ textDecoration: 'none' }} onClick={() => setActiveTab('Accueil')}>
          <div className="nav-name">HORIZON</div>
        </Link>
      </div>

      <ul className="nav-links">
        {navItems.map((item) => (
          <li key={item.name}>
            <Link 
              href={item.href} 
              className={activeTab === item.name ? 'nav-active' : ''}
              onClick={() => setActiveTab(item.name)}
            >
              {item.name}
            </Link>
          </li>
        ))}
        <li>
          <Link href="/cgu" className={activeTab === 'À propos' ? 'nav-active' : ''} onClick={() => setActiveTab('À propos')}>
            À propos
          </Link>
        </li>
      </ul>

      <div className="nav-cta">
        <Link href="/demande_compte" className={`btn-ghost-sm ${activeTab === 'Demande d\'accès' ? 'nav-active-btn' : ''}`} onClick={() => setActiveTab('Demande d\'accès')}>Demande d'accès</Link>
        <Link href="/connexion" className={`btn-primary-sm ${activeTab === 'Connexion' ? 'nav-active-btn' : ''}`} onClick={() => setActiveTab('Connexion')}>Connexion</Link>
      </div>
    </nav>
  );
};

export default Header;
