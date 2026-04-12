"use client";

import React from 'react';
import '../home.css';
import './demande.css';
import Link from 'next/link';
import Header from '../components/Header';
import Footer from '../components/Footer';

export default function DemandeCompte() {
  return (
    <div className="home-theme">
      <Header />

      <div className="request-container">
        <div className="request-card">
          
          <div className="badge-request">
            <span className="badge-dot" style={{ width: '6px', height: '6px', borderRadius: '50%', background: 'var(--cyan)', boxShadow: '0 0 8px var(--cyan)' }}></span>
            DEMANDE DE COMPTE
          </div>

          <h1 className="request-title">Horizon : Demande de création</h1>
          <p className="request-desc">
            Veuillez remplir ce formulaire avec le maximum de détails pour nous aider à évaluer votre demande d'admission.
          </p>

          <div className="request-alert">
            <svg className="form-icon" style={{ flexShrink: 0, color: '#00B4D8' }} viewBox="0 0 24 24" width="20" height="20">
              <circle cx="12" cy="12" r="10" stroke="currentColor" fill="none" strokeWidth="2"></circle>
              <line x1="12" y1="16" x2="12" y2="12" stroke="currentColor" strokeWidth="2" strokeLinecap="round"></line>
              <line x1="12" y1="8" x2="12.01" y2="8" stroke="currentColor" strokeWidth="2" strokeLinecap="round"></line>
            </svg>
            <div style={{ color: '#CBD5E1' }}>
              <strong>Remarque :</strong> Les champs marqués d'un <span style={{ color: '#00B4D8' }}>*</span> sont obligatoires. Cet espace est réservé à un <a href="#" style={{ color: '#E2E8F0', textDecoration: 'underline' }}>usage strictement académique</a> — consultez les <a href="#" style={{ color: '#E2E8F0', textDecoration: 'underline' }}>conditions d'utilisation</a> avant de soumettre.
            </div>
          </div>

          <form onSubmit={(e) => e.preventDefault()}>
            
            {/* =============== INFORMATIONS PERSONNELLES =============== */}
            <div className="divider">INFORMATIONS PERSONNELLES</div>
            <div className="form-grid">
              <div className="form-group">
                <label className="form-label">PRÉNOM <span>*</span></label>
                <div className="input-wrapper">
                  <svg className="input-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
                  <input type="text" className="form-input" placeholder="Sans accents" required />
                </div>
              </div>
              <div className="form-group">
                <label className="form-label">NOM <span>*</span></label>
                <div className="input-wrapper">
                  <svg className="input-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
                  <input type="text" className="form-input" placeholder="Sans accents" required />
                </div>
              </div>
            </div>

            <div className="form-grid">
              <div className="form-group">
                <label className="form-label">E-MAIL INSTITUTIONNEL <span>*</span></label>
                <div className="input-wrapper">
                  <svg className="input-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path><polyline points="22,6 12,13 2,6"></polyline></svg>
                  <input type="email" className="form-input" placeholder="prenom.nom@institution.cm" required />
                </div>
                <div style={{ fontSize: '12px', color: '#64748B', marginTop: '12px', lineHeight: '1.4' }}>
                  Veuillez fournir une adresse e-mail institutionnelle ou professionnelle.
                </div>
              </div>
              <div className="form-group">
                <label className="form-label">E-MAIL (CONFIRMATION) <span>(facultatif)</span></label>
                <div className="input-wrapper">
                  <svg className="input-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path><polyline points="22,6 12,13 2,6"></polyline></svg>
                  <input type="email" className="form-input" placeholder="Confirmez votre e-mail (optionnel)" />
                </div>
                <div style={{ fontSize: '12px', color: '#64748B', marginTop: '12px', lineHeight: '1.4' }}>
                  Si renseigné, les deux adresses doivent correspondre.
                </div>
              </div>
            </div>

            <div className="form-grid">
              <div className="form-group">
                <label className="form-label">NUMÉRO DE TÉLÉPHONE</label>
                <div className="input-wrapper">
                  <svg className="input-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"></path></svg>
                  <input type="tel" className="form-input" placeholder="+237 6XX XXX XXX" />
                </div>
              </div>
              <div className="form-group">
                <label className="form-label">LANGUE PRÉFÉRÉE</label>
                <div className="input-wrapper">
                  <svg className="input-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="2" y1="12" x2="22" y2="12"></line><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path></svg>
                  <select className="form-select" defaultValue="French">
                    <option value="French">Français</option>
                    <option value="English">Anglais</option>
                  </select>
                </div>
                <div style={{ fontSize: '12px', color: '#64748B', marginTop: '12px', lineHeight: '1.4' }}>
                  Sera utilisé par l'équipe technique pour vous contacter si nécessaire.
                </div>
              </div>
            </div>


            {/* =============== AFFILIATION INSTITUTIONNELLE =============== */}
            <div className="divider">AFFILIATION INSTITUTIONNELLE</div>
            <p style={{ fontSize: '14px', color: '#64748B', marginBottom: '24px' }}>
              Renseignez l'institution à laquelle vous êtes rattaché(e) pour l'utilisation de cette plateforme.
            </p>

            <div className="form-group">
              <label className="form-label">NOM DE L'INSTITUTION <span>*</span></label>
              <div className="input-wrapper">
                <svg className="input-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 10v6M2 10l10-5 10 5-10 5z"></path><path d="M6 12v5c3 3 9 3 12 0v-5"></path></svg>
                <select className="form-select" required defaultValue="">
                  <option value="" disabled>Sélectionner une institution...</option>
                  <option value="enspy">ENSPY</option>
                  <option value="unidouala">Université de Douala</option>
                  <option value="other">Autre</option>
                </select>
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">STATUT PROFESSIONNEL <span>*</span></label>
              <div className="input-wrapper">
                <svg className="input-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 10v6M2 10l10-5 10 5-10 5z"></path><path d="M6 12v5c3 3 9 3 12 0v-5"></path></svg>
                <select className="form-select" required defaultValue="">
                  <option value="" disabled>Sélectionner votre statut...</option>
                  <option value="student">Étudiant</option>
                  <option value="researcher">Chercheur</option>
                  <option value="professor">Enseignant</option>
                </select>
              </div>
            </div>


            {/* =============== PROJET & USAGE DEMANDÉ =============== */}
            <div className="divider">PROJET & USAGE DEMANDÉ</div>

            <div className="form-group">
              <label className="form-label">INTITULÉ DU PROJET <span>*</span></label>
              <div className="input-wrapper">
                <svg className="input-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>
                <input type="text" className="form-input" placeholder="Ex. : Simulation de réseaux de neurones pour la détection d'objets" required />
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">JUSTIFICATION D'USAGE <span>*</span></label>
              <div className="input-wrapper" style={{ alignItems: 'flex-start' }}>
                <svg className="input-icon" style={{ top: '20px' }} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>
                <textarea className="form-textarea" placeholder="Décrivez brièvement les ressources désirées et le but visé sur le cluster : type de calcul, OS requis, besoins en RAM/CPU, durée estimée..." required></textarea>
              </div>
              <div style={{ fontSize: '12px', color: '#64748B', marginTop: '12px' }}>
                Minimum 80 caractères. Plus la description est précise, plus votre demande a de chances d'être approuvée rapidement.
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">DESCRIPTION DÉTAILLÉE DU PROJET</label>
              <div className="input-wrapper" style={{ alignItems: 'flex-start' }}>
                 <svg className="input-icon" style={{ top: '20px' }} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>
                <textarea className="form-textarea" placeholder="Vous pouvez détailler ici les étapes du projet, la méthodologie, les données utilisées, etc."></textarea>
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">DOCUMENT DESCRIPTIF DU PROJET <span>(facultatif)</span></label>
              <div className="file-upload-area">
                <div className="upload-icon">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="17 8 12 3 7 8"></polyline><line x1="12" y1="3" x2="12" y2="15"></line></svg>
                </div>
                <div className="upload-text">CLIQUEZ POUR SÉLECTIONNER UN FICHIER</div>
                <div className="upload-hint">PDF, DOC, DOCX — MAX 10 MO</div>
                <div style={{ fontSize: '12px', color: '#64748B', marginTop: '16px' }}>
                  Un document de cadrage, une fiche de projet ou une description technique peut accélérer l'évaluation.
                </div>
              </div>
              <input type="file" style={{ display: 'none' }} />
            </div>


            {/* =============== CONDITIONS D'UTILISATION =============== */}
            <div className="divider">CONDITIONS D'UTILISATION</div>

            <div className="status-box">
              <div className="status-icon">
                <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>
              </div>
              <div className="status-text">
                La plateforme <strong>Horizon</strong> est réservée à des activités académiques et de recherche. Tout usage à des fins commerciales ou non conformes entraîne la suspension immédiate du compte. Consultez les <a href="#">usages interdits</a> dans les conditions d'utilisation.
              </div>
            </div>

            <div className="form-group" style={{ display: 'flex', alignItems: 'flex-start', gap: '16px', marginTop: '32px' }}>
              <input type="checkbox" id="rules" style={{ marginTop: '4px', width: '20px', height: '20px', cursor: 'pointer' }} required />
              <label htmlFor="rules" style={{ fontSize: '14px', color: '#94A3B8', lineHeight: '1.6' }}>
                J'ai lu et j'accepte les <a href="#" style={{ color: '#00B4D8', textDecoration: 'underline' }}>Conditions d'utilisation</a> de la plateforme Horizon, notamment les <a href="#" style={{ color: '#00B4D8', textDecoration: 'underline' }}>règles d'usage académique</a>, les <a href="#" style={{ color: '#00B4D8', textDecoration: 'underline' }}>quotas de ressources</a> et la <a href="#" style={{ color: '#00B4D8', textDecoration: 'underline' }}>politique de confidentialité</a>.
              </label>
            </div>

            <div style={{ marginTop: '48px' }}>
              <div className="divider" style={{ marginBottom: '24px' }}>SOUMETTRE LA DEMANDE</div>
              <button type="submit" className="submit-btn-primary">
                <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="white" strokeWidth="3"><path d="M22 2L11 13"></path><path d="M22 2L15 22L11 13L2 9L22 2z"></path></svg>
                ENVOYER MA DEMANDE
              </button>
            </div>

            <div style={{ textAlign: 'center', marginTop: '32px', fontSize: '14px', color: '#94A3B8' }}>
              Vous avez déjà un compte ? <Link href="/connexion" style={{ color: '#3B82F6', fontWeight: 600, textDecoration: 'none' }}>Se connecter</Link>
            </div>

          </form>
        </div>
      </div>

      <Footer />
    </div>
  );
}
