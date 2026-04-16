"use client";

import React from 'react';
import '../home.css';
import './demande.css';
import Link from 'next/link';
import Header from '../components/Header';
import Footer from '../components/Footer';
import { accountService } from '../../services/accounts';

export default function DemandeCompte() {
  const [formData, setFormData] = React.useState({
    first_name: '',
    last_name: '',
    email: '',
    phone: '',
    institution: '',
    professional_status: '',
    project_title: '',
    project_justification: '',
    project_details: '',
  });
  const [isLoading, setIsLoading] = React.useState(false);
  const [isSuccess, setIsSuccess] = React.useState(false);
  const [error, setError] = React.useState('');

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    try {
      await accountService.submitRequest({
        ...formData,
        full_name: `${formData.first_name} ${formData.last_name}`,
      });
      setIsSuccess(true);
    } catch (err: any) {
      console.error("Request submission error:", err);
      setError(err.response?.data?.detail || "Une erreur est survenue lors de la soumission. Veuillez réessayer.");
    } finally {
      setIsLoading(false);
    }
  };

  if (isSuccess) {
    return (
      <div className="home-theme">
        <Header />
        <div className="request-container" style={{ textAlign: 'center', padding: '120px 20px' }}>
          <div className="request-card">
            <div style={{ fontSize: '64px', marginBottom: '24px' }}>✅</div>
            <h1 className="request-title">Demande envoyée !</h1>
            <p className="request-desc">
              Merci {formData.first_name}. Votre demande de création de compte Horizon a bien été reçue.
              Elle sera examinée par notre équipe technique. Un e-mail de confirmation vous sera envoyé prochainement.
            </p>
            <Link href="/" className="submit-btn-primary" style={{ display: 'inline-flex', marginTop: '32px', textDecoration: 'none' }}>
              RETOURNER À L'ACCUEIL
            </Link>
          </div>
        </div>
        <Footer />
      </div>
    );
  }

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

          {error && (
            <div className="request-alert" style={{ background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.2)', color: '#ef4444' }}>
              <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
              <div>{error}</div>
            </div>
          )}

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

          <form onSubmit={handleSubmit}>

            {/* =============== INFORMATIONS PERSONNELLES =============== */}
            <div className="divider">INFORMATIONS PERSONNELLES</div>
            <div className="form-grid">
              <div className="form-group">
                <label className="form-label">PRÉNOM <span>*</span></label>
                <div className="input-wrapper">
                  <svg className="input-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
                  <input type="text" className="form-input" name="first_name" value={formData.first_name} onChange={handleChange} placeholder="Sans accents" required disabled={isLoading} />
                </div>
              </div>
              <div className="form-group">
                <label className="form-label">NOM <span>*</span></label>
                <div className="input-wrapper">
                  <svg className="input-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
                  <input type="text" className="form-input" name="last_name" value={formData.last_name} onChange={handleChange} placeholder="Sans accents" required disabled={isLoading} />
                </div>
              </div>
            </div>

            <div className="form-grid">
              <div className="form-group">
                <label className="form-label">E-MAIL INSTITUTIONNEL <span>*</span></label>
                <div className="input-wrapper">
                  <svg className="input-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path><polyline points="22,6 12,13 2,6"></polyline></svg>
                  <input type="email" className="form-input" name="email" value={formData.email} onChange={handleChange} placeholder="prenom.nom@institution.cm" required disabled={isLoading} />
                </div>
                <div style={{ fontSize: '12px', color: '#64748B', marginTop: '12px', lineHeight: '1.4' }}>
                  Veuillez fournir une adresse e-mail institutionnelle ou professionnelle.
                </div>
              </div>
              <div className="form-group">
                <label className="form-label">NUMÉRO DE TÉLÉPHONE</label>
                <div className="input-wrapper">
                  <svg className="input-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"></path></svg>
                  <input type="tel" className="form-input" name="phone" value={formData.phone} onChange={handleChange} placeholder="+237 6XX XXX XXX" disabled={isLoading} />
                </div>
              </div>
            </div>


            {/* =============== AFFILIATION INSTITUTIONNELLE =============== */}
            <div className="divider">AFFILIATION INSTITUTIONNELLE</div>

            <div className="form-group">
              <label className="form-label">NOM DE L'INSTITUTION <span>*</span></label>
              <div className="input-wrapper">
                <svg className="input-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 10v6M2 10l10-5 10 5-10 5z"></path><path d="M6 12v5c3 3 9 3 12 0v-5"></path></svg>
                <select className="form-select" name="institution" value={formData.institution} onChange={handleChange} required disabled={isLoading}>
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
                <select className="form-select" name="professional_status" value={formData.professional_status} onChange={handleChange} required disabled={isLoading}>
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
                <input type="text" className="form-input" name="project_title" value={formData.project_title} onChange={handleChange} placeholder="Ex. : Simulation de réseaux de neurones pour la détection d'objets" required disabled={isLoading} />
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">JUSTIFICATION D'USAGE <span>*</span></label>
              <div className="input-wrapper" style={{ alignItems: 'flex-start' }}>
                <svg className="input-icon" style={{ top: '20px' }} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>
                <textarea className="form-textarea" name="project_justification" value={formData.project_justification} onChange={handleChange} placeholder="Décrivez brièvement les ressources désirées et le but visé sur le cluster : type de calcul, OS requis, besoins en RAM/CPU, durée estimée..." required disabled={isLoading}></textarea>
              </div>
            </div>

            <div className="form-group" style={{ display: 'flex', alignItems: 'flex-start', gap: '16px', marginTop: '32px' }}>
              <input type="checkbox" id="rules" style={{ marginTop: '4px', width: '20px', height: '20px', cursor: 'pointer' }} required disabled={isLoading} />
              <label htmlFor="rules" style={{ fontSize: '14px', color: '#94A3B8', lineHeight: '1.6' }}>
                J'ai lu et j'accepte les <a href="#" style={{ color: '#00B4D8', textDecoration: 'underline' }}>Conditions d'utilisation</a> de la plateforme Horizon.
              </label>
            </div>

            <div style={{ marginTop: '48px' }}>
              <button type="submit" className="submit-btn-primary" disabled={isLoading}>
                {isLoading ? (
                  <span>CHARGEMENT...</span>
                ) : (
                  <>
                    <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="white" strokeWidth="3"><path d="M22 2L11 13"></path><path d="M22 2L15 22L11 13L2 9L22 2z"></path></svg>
                    ENVOYER MA DEMANDE
                  </>
                )}
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
