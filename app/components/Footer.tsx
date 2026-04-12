"use client";
import React from 'react';
import Link from 'next/link';

const Footer = () => (
  <footer className="footer-professional">
    <div className="footer-top">
      <div className="footer-col brand-col">
        <div className="footer-brand">
          <div className="footer-logo">
            <svg viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <rect x="2" y="3" width="8" height="8" rx="1"/>
              <rect x="14" y="3" width="8" height="8" rx="1"/>
              <rect x="2" y="13" width="8" height="8" rx="1"/>
              <rect x="14" y="13" width="8" height="8" rx="1"/>
            </svg>
          </div>
          <div className="footer-name">HORIZON</div>
        </div>
        <p className="footer-desc">
          Infrastructure Cloud académique pour la communauté de l'ENSPY.
          Mettez la puissance du digital au service de vos projets de recherche et de développement.
        </p>
      </div>

      <div className="footer-col">
        <h4 className="footer-heading">Plateforme</h4>
        <ul className="footer-links">
          <li><Link href="/#features">Fonctionnalités</Link></li>
          <li><Link href="/#how">Comment ça marche</Link></li>
          <li><Link href="/#about">À propos</Link></li>
          <li><Link href="/cgu">Conditions d'utilisation</Link></li>
          <li><Link href="/demande_compte">Demander un accès</Link></li>
        </ul>
      </div>

      <div className="footer-col">
        <h4 className="footer-heading">Ressources</h4>
        <ul className="footer-links">
          <li><a href="#">Documentation</a></li>
          <li><a href="#">Tutoriels</a></li>
          <li><a href="#">Support technique</a></li>
          <li><a href="#">Statut du réseau</a></li>
        </ul>
      </div>

      <div className="footer-col">
        <h4 className="footer-heading">Contact & Légal</h4>
        <ul className="footer-links">
          <li><a href="#">contact@horizon-enspy.cm</a></li>
          <li><a href="#">Mentions légales</a></li>
          <li><a href="#">Confidentialité</a></li>
        </ul>
      </div>
    </div>

    <div className="footer-bottom">
      <div className="footer-copyright">
        © 2025 Équipe Horizon · ENSPY · Tous droits réservés.
      </div>
      <div className="footer-socials">
        <a href="#" aria-label="GitHub">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22"/></svg>
        </a>
        <a href="#" aria-label="LinkedIn">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z"/><rect x="2" y="9" width="4" height="12"/><circle cx="4" cy="4" r="2"/></svg>
        </a>
        <a href="#" aria-label="Twitter">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M23 3a10.9 10.9 0 0 1-3.14 1.53 4.48 4.48 0 0 0-7.86 3v1A10.66 10.66 0 0 1 3 4s-4 9 5 13a11.64 11.64 0 0 1-7 2c9 5 20 0 20-11.5a4.5 4.5 0 0 0-.08-.83A7.72 7.72 0 0 0 23 3z"/></svg>
        </a>
      </div>
    </div>
  </footer>
);

export default Footer;
