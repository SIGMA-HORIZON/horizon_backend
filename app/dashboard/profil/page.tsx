"use client";
import { useAuth } from '../../../context/AuthContext';
import { useVMs } from '../VMContext';

export default function Profil() {
  const { user } = useAuth();
  const { vms } = useVMs();

  // Initiales pour l'avatar
  const initiales = `${user?.first_name?.[0] || ''}${user?.last_name?.[0] || ''}`.toUpperCase() || '??';

  // Stats calculées
  const activeVMs = vms.filter(v => v.status === 'on' || v.status === 'warn').length;
  const totalVMs = vms.length;
  const totalStorage = vms.reduce((acc, v) => acc + (v.storage_gb || 0), 0);

  // Date d'adhésion
  const memberSince = user?.created_at
    ? new Date(user.created_at).toLocaleDateString('fr-FR', { month: 'long', year: 'numeric' })
    : 'mars 2025';

  return (
    <div className="page active" id="pg-profil" style={{ padding: '0 20px 40px' }}>

      <div style={{ marginBottom: '32px' }}>
        <h1 style={{ fontSize: '28px', fontWeight: 700, color: 'var(--g1-text)', marginBottom: '8px', letterSpacing: '-0.5px' }}>Mon profil</h1>
        <p style={{ color: 'var(--g1-muted)', fontSize: '15px' }}>Gérez vos informations personnelles, e-mail et mot de passe.</p>
      </div>

      <div className="profil-layout">

        {/* COLONNE GAUCHE */}
        <div className="prof-left">

          <div className="pro-card">
            <div className="pro-av">
              {initiales}
              <div className="pro-av-edit">
                <svg viewBox="0 0 24 24"><path d="M12 20h9" /><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z" /></svg>
              </div>
            </div>
            <div className="pro-name">{user?.first_name} {user?.last_name}</div>
            <div className="pro-email">{user?.email}</div>

            <div className="pro-badge">
              <span style={{ color: 'var(--g1-on)', marginRight: '6px' }}>●</span>
              {user?.role === 'SUPER_ADMIN' ? 'ADMINISTRATEUR SIGMA' : user?.role === 'ADMIN' ? 'ADMINISTRATEUR' : 'UTILISATEUR HORIZON'}
            </div>

            <div className="pro-stats">
              <div className="pro-stat-box">
                <div className="pro-stat-val">{activeVMs}</div>
                <div className="pro-stat-lbl">VMs Actives</div>
              </div>
              <div className="pro-stat-box">
                <div className="pro-stat-val">{totalVMs}</div>
                <div className="pro-stat-lbl">VMs Créées</div>
              </div>
              <div className="pro-stat-box">
                <div className="pro-stat-val">--</div>
                <div className="pro-stat-lbl">Temps Total</div>
              </div>
              <div className="pro-stat-box">
                <div className="pro-stat-val">{totalStorage}<span style={{ fontSize: '14px' }}>Go</span></div>
                <div className="pro-stat-lbl">Stockage Utilisé</div>
              </div>
            </div>

            <div className="pro-member-since">
              <svg viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="18" rx="2" ry="2" /><line x1="16" y1="2" x2="16" y2="6" /><line x1="8" y1="2" x2="8" y2="6" /><line x1="3" y1="10" x2="21" y2="10" /></svg>
              Membre depuis {memberSince}
            </div>

          </div>
        </div>

        {/* COLONNE PRINCIPALE */}
        <div className="prof-main">

          {/* Card: Infos */}
          <div className="pm-card">
            <div className="pm-hdr">
              <svg viewBox="0 0 24 24"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" /><circle cx="12" cy="7" r="4" /></svg>
              Informations personnelles
            </div>
            <div className="pm-body">
              <div className="pm-row">
                <div className="pm-field">
                  <label className="pm-label">Nom</label>
                  <div className="pm-input-wrap">
                    <svg className="pm-input-icon" viewBox="0 0 24 24"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" /><circle cx="12" cy="7" r="4" /></svg>
                    <input className="pm-input" type="text" defaultValue={user?.last_name || ''} />
                  </div>
                </div>
                <div className="pm-field">
                  <label className="pm-label">Prénom</label>
                  <div className="pm-input-wrap">
                    <svg className="pm-input-icon" viewBox="0 0 24 24"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" /><circle cx="12" cy="7" r="4" /></svg>
                    <input className="pm-input" type="text" defaultValue={user?.first_name || ''} />
                  </div>
                </div>
              </div>
              <div className="pm-field">
                <label className="pm-label">Organisation</label>
                <div className="pm-input-wrap">
                  <svg className="pm-input-icon" viewBox="0 0 24 24"><rect x="2" y="7" width="20" height="14" rx="2" ry="2" /><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16" /></svg>
                  <input className="pm-input" type="text" defaultValue={user?.organisation || ''} disabled />
                  <div className="pm-input-badge">ADMIN ONLY</div>
                </div>
              </div>
              <div className="pm-field">
                <label className="pm-label">Niveau / Statut</label>
                <div className="pm-input-wrap">
                  <svg className="pm-input-icon" viewBox="0 0 24 24"><path d="M22 10v6M2 10l10-5 10 5-10 5z" /><path d="M6 12v5c3 3 9 3 12 0v-5" /></svg>
                  <input className="pm-input" type="text" defaultValue={user?.role === 'SUPER_ADMIN' ? 'Admin Système' : 'Étudiant'} disabled />
                  <div className="pm-input-badge">ADMIN ONLY</div>
                </div>
              </div>
              <div className="pm-alert">
                <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10" /><line x1="12" y1="16" x2="12" y2="12" /><line x1="12" y1="8" x2="12.01" y2="8" /></svg>
                <p>Le nom, l'organisation et le statut ne peuvent être modifiés que par un administrateur. Contactez l'équipe Horizon pour toute correction.</p>
              </div>
            </div>
          </div>

          {/* Card: Email */}
          <div className="pm-card">
            <div className="pm-hdr">
              <svg viewBox="0 0 24 24"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" /><polyline points="22,6 12,13 2,6" /></svg>
              Adresse e-mail
            </div>
            <div className="pm-body">
              <div className="pm-field">
                <label className="pm-label">E-mail Actuel</label>
                <div className="pm-input-wrap">
                  <svg className="pm-input-icon" viewBox="0 0 24 24"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" /><polyline points="22,6 12,13 2,6" /></svg>
                  <input className="pm-input" type="text" defaultValue={user?.email || ''} disabled />
                </div>
              </div>
              <div className="pm-field">
                <label className="pm-label">Nouvel E-mail</label>
                <div className="pm-input-wrap">
                  <svg className="pm-input-icon" viewBox="0 0 24 24"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" /><polyline points="22,6 12,13 2,6" /></svg>
                  <input className="pm-input" type="email" placeholder="nouveau@enspy.cm" />
                </div>
              </div>
              <div className="pm-field">
                <label className="pm-label">Confirmer l'E-mail</label>
                <div className="pm-input-wrap">
                  <svg className="pm-input-icon" viewBox="0 0 24 24"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" /><polyline points="22,6 12,13 2,6" /></svg>
                  <input className="pm-input" type="email" placeholder="nouveau@enspy.cm" />
                </div>
              </div>
              <div className="pm-actions">
                <button className="btn-ghost">Annuler</button>
                <button className="btn-primary">
                  <svg viewBox="0 0 24 24"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z" /><polyline points="17 21 17 13 7 13 7 21" /><polyline points="7 3 7 8 15 8" /></svg>
                  Enregistrer l'e-mail
                </button>
              </div>
            </div>
          </div>

          {/* Card: Password */}
          <div className="pm-card">
            <div className="pm-hdr">
              <svg viewBox="0 0 24 24"><rect x="3" y="11" width="18" height="11" rx="2" ry="2" /><path d="M7 11V7a5 5 0 0 1 10 0v4" /></svg>
              Mot de passe
            </div>
            <div className="pm-body">
              <div className="pm-field">
                <label className="pm-label">Mot de passe actuel</label>
                <div className="pm-input-wrap">
                  <svg className="pm-input-icon" viewBox="0 0 24 24"><rect x="3" y="11" width="18" height="11" rx="2" ry="2" /><path d="M7 11V7a5 5 0 0 1 10 0v4" /></svg>
                  <input className="pm-input" type="password" placeholder="••••••••••••" />
                </div>
              </div>
              <div className="pm-row">
                <div className="pm-field">
                  <label className="pm-label">Nouveau mot de passe</label>
                  <div className="pm-input-wrap">
                    <svg className="pm-input-icon" viewBox="0 0 24 24"><rect x="3" y="11" width="18" height="11" rx="2" ry="2" /><path d="M7 11V7a5 5 0 0 1 10 0v4" /></svg>
                    <input className="pm-input" type="password" placeholder="Min. 10 caractères" />
                  </div>
                </div>
                <div className="pm-field">
                  <label className="pm-label">Confirmer le mot de passe</label>
                  <div className="pm-input-wrap">
                    <svg className="pm-input-icon" viewBox="0 0 24 24"><rect x="3" y="11" width="18" height="11" rx="2" ry="2" /><path d="M7 11V7a5 5 0 0 1 10 0v4" /></svg>
                    <input className="pm-input" type="password" placeholder="Répétez le mot de passe" />
                  </div>
                </div>
              </div>
              <div className="pm-alert pm-alert-warn">
                <svg viewBox="0 0 24 24"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" /><line x1="12" y1="9" x2="12" y2="13" /><line x1="12" y1="17" x2="12.01" y2="17" /></svg>
                <p>10 caractères minimum : majuscule, chiffre, caractère spécial requis. Toute tentative échouée est journalisée.</p>
              </div>
            </div>
          </div>

          {/* Card: Recent Activity */}
          <div className="pm-card">
            <div className="pm-hdr">
              <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10" /><polyline points="12 6 12 12 16 14" /></svg>
              Activité récente du compte
            </div>
            <div className="pm-body" style={{ padding: '24px' }}>
              <div className="act-list">

                <div className="act-item">
                  <div className="act-dot" style={{ background: 'var(--g1-on)' }}></div>
                  <div className="act-content">
                    <h4>Connexion réussie</h4>
                    <p>IP 196.200.12.45 &nbsp; Aujourd'hui, 07:38</p>
                  </div>
                </div>

                <div className="act-item">
                  <div className="act-dot" style={{ background: '#00B4D8' }}></div>
                  <div className="act-content">
                    <h4>VM ubuntu-ml-test démarrée</h4>
                    <p>Nœud REM &nbsp; Hier, 14:22</p>
                  </div>
                </div>

                <div className="act-item">
                  <div className="act-dot" style={{ background: 'var(--g1-warn)' }}></div>
                  <div className="act-content">
                    <h4>Tentative de connexion échouée</h4>
                    <p>IP 41.202.8.110 &nbsp; Hier, 09:05</p>
                  </div>
                </div>

                <div className="act-item">
                  <div className="act-dot" style={{ background: 'var(--g1-on)' }}></div>
                  <div className="act-content">
                    <h4>Mot de passe modifié</h4>
                    <p>Via portail Horizon &nbsp; 28 mars 2025</p>
                  </div>
                </div>

              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
  )
}
