"use client";

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import '../home.css';
import './cgu.css';
import Header from '../components/Header';
import Footer from '../components/Footer';

export default function CGUPage() {
  const [isSectionOpen, setIsSectionOpen] = useState(true);
  const [activeSection, setActiveSection] = useState('intro');
  const [scrollProgress, setScrollProgress] = useState(0);

  useEffect(() => {
    const handleScroll = () => {
      // Progress Bar
      const docHeight = document.documentElement.scrollHeight - window.innerHeight;
      const scrollTop = window.scrollY;
      setScrollProgress(docHeight > 0 ? (scrollTop / docHeight) * 100 : 0);

      // Scroll Spy
      const sections = ['intro', 'objet', 'acces', 'usages', 'ressources', 'securite', 'donnees', 'obligations', 'sanctions', 'responsabilites', 'modifications', 'contact'];
      let currentSection = 'intro';

      for (const id of sections) {
        const element = document.getElementById(id);
        if (element) {
          const rect = element.getBoundingClientRect();
          if (rect.top <= 100) {
            currentSection = id;
          }
        }
      }
      setActiveSection(currentSection);
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    handleScroll(); // init

    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <div className="home-theme cgu-theme">
      <div className="progress-bar"><div className="progress-fill" style={{ width: `${scrollProgress}%` }}></div></div>

      <Header />

      <div className="cgu-page-wrap">
        
        {/* SIDEBAR */}
        <aside className="cgu-sidebar">
          <div className="sb-header">
            <div className="sb-header-top">
              <div className="sb-header-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
              </div>
              <span className="sb-title">Conditions d'utilisation</span>
            </div>
          </div>

          <div className="sb-section">
            <button className={`sb-section-toggle ${isSectionOpen ? 'open' : ''}`} onClick={() => setIsSectionOpen(!isSectionOpen)}>
              Les conditions d'utilisation
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="6 9 12 15 18 9"/></svg>
            </button>
            <div className={`sb-links ${isSectionOpen ? '' : 'collapsed'}`}>
              {[
                { id: 'intro', label: 'Introduction' },
                { id: 'objet', label: 'Objet et champ d\'application' },
                { id: 'acces', label: 'Accès à la plateforme' },
                { id: 'usages', label: 'Usages autorisés et interdits' },
                { id: 'ressources', label: 'Ressources et quotas' },
                { id: 'securite', label: 'Sécurité et authentification' },
                { id: 'donnees', label: 'Données personnelles' },
                { id: 'obligations', label: 'Obligations de l\'utilisateur' },
                { id: 'sanctions', label: 'Sanctions et suspension' },
                { id: 'responsabilites', label: 'Responsabilités' },
                { id: 'modifications', label: 'Modifications des conditions' },
                { id: 'contact', label: 'Contact et réclamations' }
              ].map(item => (
                <a 
                  key={item.id}
                  className={`sb-link ${activeSection === item.id ? 'active' : ''}`} 
                  href={`#${item.id}`}
                  onClick={(e) => {
                    e.preventDefault();
                    document.getElementById(item.id)?.scrollIntoView({ behavior: 'smooth' });
                  }}
                >
                  {item.label}
                </a>
              ))}
            </div>
          </div>

          <div className="sb-footer">
            <div>Version 1.0 — Avril 2025<br/>Équipe Horizon · ENSPY</div>
            <Link href="/demande_compte">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
              Demander un accès
            </Link>
          </div>
        </aside>

        {/* MAIN CONTENT */}
        <main className="main-content">
          
          <div className="cgu-hero" id="intro">
            <div className="hero-badge"><span className="badge-pulse"></span>Document officiel</div>
            <h1>Conditions d'utilisation<br/>de la plateforme Horizon</h1>
            <p className="hero-lead">
              Ces conditions régissent l'utilisation d'<strong>Horizon</strong>, système de gestion de machines virtuelles Cloud, développé pour l'ENSPY. En accédant à la plateforme ou en soumettant une <Link href="/demande_compte">demande de compte</Link>, vous acceptez l'intégralité des présentes conditions.
            </p>
            <div className="meta-chips">
              <div className="meta-chip">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
                Entrée en vigueur : Avril 2025
              </div>
              <div className="meta-chip">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/></svg>
                Équipe Horizon — ENSPY
              </div>
              <div className="meta-chip">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
                Cluster Principal
              </div>
            </div>
          </div>

          <section className="cgu-section" id="objet">
            <h2 className="section-title">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
              Objet et champ d'application
            </h2>
            <p className="body-text"><strong>Horizon</strong> est un système de gestion de machines virtuelles (VMs) qui donne accès aux ressources cloud partagées composées des nœuds de calcul et de stockage.</p>
            <p className="body-text">Les présentes conditions s'appliquent à toute personne qui soumet une <Link href="/demande_compte">demande d'accès</Link>, crée un compte ou utilise les services de la plateforme Horizon.</p>
            <div className="cgu-alert alert-info">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
              <span>L'utilisation de la plateforme est strictement réservée à des fins <strong>académiques et de recherche</strong>. Consultez les <a href="#usages">usages autorisés et interdits</a> pour plus de détails.</span>
            </div>
            <div className="section-end"></div>
          </section>

          <section className="cgu-section" id="acces">
            <h2 className="section-title">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
              Accès à la plateforme
            </h2>
            <div className="sub-heading">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
              Processus de demande
            </div>
            <p className="body-text">L'accès à Horizon est conditionné à la validation préalable d'une <Link href="/demande_compte">demande de création de compte</Link> par un administrateur. Aucune auto-inscription n'est permise.</p>
            <ul className="doc-list">
              <li>L'utilisateur soumet un formulaire de demande comprenant ses informations personnelles, son affiliation institutionnelle et une justification d'usage.</li>
              <li>Un administrateur examine la demande et peut l'approuver ou la rejeter sans obligation de motivation.</li>
              <li>En cas d'approbation, des identifiants provisoires sont transmis à l'adresse fournie.</li>
              <li>L'utilisateur est tenu de modifier son mot de passe provisoire dès la première connexion.</li>
            </ul>

            <div className="sub-divider"></div>

            <div className="sub-heading">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>
              Révocation de l'accès
            </div>
            <p className="body-text">L'accès peut être révoqué à tout moment par un administrateur, notamment en cas de violation des présentes conditions (voir <a href="#sanctions">sanctions</a>) ou d'inactivité prolongée.</p>
            <div className="section-end"></div>
          </section>

          {/* ADD OTHER SECTIONS */}
          <section className="cgu-section" id="usages">
            <h2 className="section-title">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M9 12l2 2 4-4"/><path d="M21 12c0 4.97-4.03 9-9 9S3 16.97 3 12 7.03 3 12 3s9 4.03 9 9z"/></svg>
              Usages autorisés et interdits
            </h2>

            <div className="sub-heading">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
              Usages autorisés
            </div>
            <ul className="doc-list">
              <li>Travaux pratiques, simulations et expériences dans le cadre de cours universitaires.</li>
              <li>Projets de recherche académique, thèses, mémoires de master ou de doctorat.</li>
              <li>Développement et test de logiciels à des fins éducatives ou de recherche.</li>
              <li>Traitement de données dans le cadre de projets approuvés par l'institution.</li>
            </ul>

            <div className="sub-divider"></div>

            <div className="sub-heading">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>
              Usages strictement interdits
            </div>
            <div className="cgu-alert alert-danger">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
              <span>Tout manquement à ces interdictions entraîne des sanctions immédiates pouvant aller jusqu'à la suspension définitive du compte.</span>
            </div>
            <ul className="doc-list">
              <li><strong>Minage de cryptomonnaies</strong> — toute exploitation des ressources à cette fin est interdite.</li>
              <li><strong>Activités commerciales</strong> — utilisation générant des revenus personnels directs ou indirects.</li>
              <li><strong>Stockage ou distribution de contenus illégaux</strong> — y compris les logiciels piratés et tout contenu contrevenant à la législation.</li>
              <li><strong>Attaques réseau</strong> — port scanning, exploitation de vulnérabilités, tentatives d'intrusion depuis une VM.</li>
              <li><strong>Partage des identifiants</strong> — il est interdit de transmettre ses accès à un tiers.</li>
              <li><strong>Modification de l'infrastructure physique</strong> — accès aux paramètres firmware réservé aux admins.</li>
              <li><strong>Accès aux VMs d'autres utilisateurs</strong> — chaque VM appartient exclusivement à son créateur.</li>
            </ul>
            <div className="section-end"></div>
          </section>

          <section className="cgu-section" id="ressources">
            <h2 className="section-title">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 20V10M12 20V4M6 20v-6"/></svg>
              Ressources et quotas
            </h2>

            <div className="sub-heading">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M3 15h18M9 3v18"/></svg>
              Quotas par défaut
            </div>
            <table className="quota-table">
              <thead>
                <tr><th>Ressource</th><th>Valeur par défaut</th><th>Maximum autorisé</th></tr>
              </thead>
              <tbody>
                <tr><td>CPU (vCores) par VM</td><td>2 vCores</td><td>8 vCores</td></tr>
                <tr><td>RAM par VM</td><td>2 Go</td><td>16 Go</td></tr>
                <tr><td>Stockage (ROM) par VM</td><td>20 Go</td><td>100 Go</td></tr>
                <tr><td>VMs simultanées</td><td>2 VMs</td><td>5 VMs</td></tr>
              </tbody>
            </table>

            <div className="sub-divider"></div>

            <div className="sub-heading">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
              Nettoyage automatique
            </div>
            <ul className="doc-list">
              <li>Toute VM inactive depuis plus de <strong>2 heures</strong> déclenche une alerte e-mail.</li>
              <li>Une VM arrêtée depuis plus de <strong>7 jours</strong> est supprimée automatiquement.</li>
              <li>L'utilisateur est <strong>responsable d'arrêter ses VMs</strong> dès qu'elles ne sont plus utilisées.</li>
            </ul>
            <div className="section-end"></div>
          </section>

          <section className="cgu-section" id="securite">
            <h2 className="section-title">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
              Sécurité et authentification
            </h2>
            <p className="body-text">L'utilisateur est seul responsable de la confidentialité de ses identifiants. Toute utilisation du compte sous son identité lui est imputable, sauf preuve de compromission signalée dans les meilleurs délais.</p>
            <ul className="doc-list">
              <li>Le mot de passe doit contenir au moins <strong>10 caractères</strong>, une majuscule, un chiffre et un caractère spécial.</li>
              <li>Toute tentative d'accès non autorisé ou de contournement des mécanismes de journalisation est une violation grave.</li>
            </ul>
            <div className="section-end"></div>
          </section>

          <section className="cgu-section" id="donnees">
            <h2 className="section-title">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
              Données personnelles
            </h2>
            <p className="body-text">Les données personnelles collectées sont utilisées exclusivement pour la gestion des comptes et la sécurité de la plateforme. Elles ne sont ni vendues, ni partagées avec des tiers.</p>
            <div className="section-end"></div>
          </section>

          <section className="cgu-section" id="obligations">
            <h2 className="section-title">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/></svg>
              Obligations de l'utilisateur
            </h2>
            <ul className="doc-list">
              <li>Utiliser les ressources uniquement dans le cadre défini dans sa demande d'accès.</li>
              <li>Respecter les licences des systèmes et logiciels déployés sur ses VMs.</li>
              <li>Ne pas stocker de données personnelles de tiers sur les espaces partagés.</li>
            </ul>
            <div className="section-end"></div>
          </section>

          <section className="cgu-section" id="sanctions">
            <h2 className="section-title">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
              Sanctions et suspension
            </h2>
            <p className="body-text">Tout manquement entraîne des sanctions proportionnées :</p>
            <div className="sanction-cards">
              <div className="sanction-card">
                <div className="s-level level-1">Niveau 1<br/>(Avert.)</div>
                <div className="s-col">Quota mineur dépassé</div>
                <div className="s-col">Avertissement automatique</div>
              </div>
              <div className="sanction-card">
                <div className="s-level level-2">Niveau 2<br/>(Suspens.)</div>
                <div className="s-col">Violation répétée</div>
                <div className="s-col">Suspension temporaire (24h)</div>
              </div>
              <div className="sanction-card">
                <div className="s-level level-3">Niveau 3<br/>(Excl.)</div>
                <div className="s-col">Incident grave (minage, fraudes)</div>
                <div className="s-col">Suspension immédiate + possible suppression</div>
              </div>
            </div>
            <div className="section-end"></div>
          </section>

          <section className="cgu-section" id="responsabilites">
            <h2 className="section-title">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
              Responsabilités
            </h2>
            <p className="body-text">L'équipe s'engage à maintenir une disponibilité de 99% mais n'est pas responsable des pertes de données résultant de la maintenance automatique ou d'un usage non conforme.</p>
            <div className="section-end"></div>
          </section>

          <section className="cgu-section" id="modifications">
            <h2 className="section-title">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
              Modifications
            </h2>
            <p className="body-text">L'équipe se réserve le droit de modifier ces conditions, avec un préavis d'au moins 7 jours par email aux utilisateurs actifs.</p>
            <div className="section-end"></div>
          </section>

          <section className="cgu-section" id="contact">
            <h2 className="section-title">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
              Contact
            </h2>
            <p className="body-text">Pour toute question, demande de suppression des données, ou problème de sécurité, contactez l'équipe Horizon à contact@horizon-enspy.cm.</p>
            <div className="section-end"></div>
          </section>

          <div className="accept-footer">
            <h2>Prêt à rejoindre la plateforme ?</h2>
            <p>En remplissant votre formulaire de demande, vous confirmez avoir lu et accepté ces conditions.</p>
            <Link href="/demande_compte" className="btn-primary">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
              Faire une demande d'accès
            </Link>
            <Link href="/connexion" className="btn-ghost">Déjà un compte ? Se connecter</Link>
          </div>

        </main>
      </div>

      <Footer />
    </div>
  );
}
