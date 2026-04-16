"use client";

import React, { useState } from 'react';
import '../home.css';
import './connexion.css';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import Header from '../components/Header';
import Footer from '../components/Footer';
import { useAuth } from '../../context/AuthContext';

export default function Connexion() {
  const router = useRouter();
  const { login } = useAuth();
  const [showPassword, setShowPassword] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      const data = await login(email, password);
      if (data.must_change_pwd) {
        router.push('/mon-profil-use/change-password'); // À adapter selon la structure réelle
      } else {
        router.push((data.role === 'ADMIN' || data.role === 'SUPER_ADMIN') ? '/admin' : '/dashboard');
      }
    } catch (err: any) {
      console.error("Login error:", err);
      setError(err.response?.data?.detail || "Identifiants invalides ou erreur de connexion.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="home-theme">
      {/* Background gradients and grid handled by .home-theme in home.css */}
      <link rel="preconnect" href="https://fonts.googleapis.com" />
      <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
      <link
        href="https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;500;600;700&family=DM+Sans:opsz,wght@9..40,300;9..40,400;9..40,500;9..40,600&display=swap"
        rel="stylesheet"
      />

      <Header />

      <div className="login-container" style={{ padding: '120px 20px 80px' }}>
        <div className="login-card">
          <div className="badge-secure">
            <span className="badge-dot" style={{ width: '6px', height: '6px', borderRadius: '50%', background: 'var(--cyan)', boxShadow: '0 0 8px var(--cyan)' }}></span>
            CONNEXION SÉCURISÉE
          </div>

          <h1 className="login-title">Accédez à votre espace</h1>
          <p className="login-desc">
            Utilisez les identifiants provisoires reçus par e-mail. Vous serez invité à changer votre mot de passe à la première connexion.
          </p>

          {error && (
            <div className="login-alert" style={{ background: 'rgba(239, 68, 68, 0.1)', color: '#ef4444', borderColor: 'rgba(239, 68, 68, 0.2)' }}>
              <svg className="form-icon" style={{ flexShrink: 0, color: '#ef4444' }} viewBox="0 0 24 24">
                <circle cx="12" cy="12" r="10"></circle>
                <line x1="12" y1="8" x2="12" y2="12"></line>
                <line x1="12" y1="16" x2="12.01" y2="16"></line>
              </svg>
              <div>{error}</div>
            </div>
          )}

          <div className="login-alert">
            <svg className="form-icon" style={{ flexShrink: 0, color: 'var(--cyan)' }} viewBox="0 0 24 24">
              <circle cx="12" cy="12" r="10"></circle>
              <line x1="12" y1="16" x2="12" y2="12"></line>
              <line x1="12" y1="8" x2="12.01" y2="8"></line>
            </svg>
            <div>
              Vos identifiants vous ont été communiqués par e-mail suite à la validation de votre demande d'accès.
            </div>
          </div>

          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label className="form-label">ADRESSE E-MAIL</label>
              <div className="input-wrapper">
                <svg className="input-icon form-icon" viewBox="0 0 24 24">
                  <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path>
                  <polyline points="22,6 12,13 2,6"></polyline>
                </svg>
                <input
                  type="email"
                  className="form-input"
                  placeholder="jean.dupont@enspy.cm"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  disabled={isLoading}
                />
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">MOT DE PASSE</label>
              <div className="input-wrapper">
                <svg className="input-icon form-icon" viewBox="0 0 24 24">
                  <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
                  <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
                </svg>
                <input
                  type={showPassword ? 'text' : 'password'}
                  className="form-input"
                  placeholder="Mot de passe provisoire"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  disabled={isLoading}
                />
                <div
                  className="input-icon-right"
                  onClick={() => setShowPassword(!showPassword)}
                >
                  {showPassword ? (
                    <svg className="form-icon" viewBox="0 0 24 24">
                      <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path>
                      <line x1="1" y1="1" x2="23" y2="23"></line>
                    </svg>
                  ) : (
                    <svg className="form-icon" viewBox="0 0 24 24">
                      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                      <circle cx="12" cy="12" r="3"></circle>
                    </svg>
                  )}
                </div>
              </div>
            </div>

            <div className="form-row">
              <label className="checkbox-wrapper">
                <input type="checkbox" className="custom-checkbox" />
                <span>Se souvenir de moi</span>
              </label>
              <a href="#" className="forgot-link">
                Mot de passe oublié ?
              </a>
            </div>

            <div className="divider">CONNEXION</div>

            <button type="submit" className="login-btn-primary" disabled={isLoading}>
              {isLoading ? (
                <span className="loader-small"></span>
              ) : (
                <svg className="form-icon" viewBox="0 0 24 24">
                  <line x1="5" y1="12" x2="19" y2="12"></line>
                  <polyline points="12 5 19 12 12 19"></polyline>
                </svg>
              )}
              <span>{isLoading ? 'Connexion en cours...' : 'Se connecter'}</span>
            </button>
          </form>

          <div className="login-footer">
            Vous n'avez pas encore de compte ?
            <Link href="/demande_compte">
              Faire une demande d'accès
            </Link>
          </div>
        </div>
      </div>

      <Footer />
    </div>
  );
}
