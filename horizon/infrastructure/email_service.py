"""Envoi d'e-mails (mock ou SMTP)."""

import logging
import smtplib
import ssl
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from horizon.core.config import get_settings

logger = logging.getLogger("horizon.email")
settings = get_settings()

# Placeholder pour le logo officiel (doit être hébergé sur un serveur public)
LOGO_URL = "https://horizon.enspy.cm/static/logo.png"


def _build_message(to: str, subject: str, body_html: str) -> MIMEMultipart:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{settings.EMAIL_FROM_NAME} <{settings.EMAIL_FROM}>"
    msg["To"] = to
    msg.attach(MIMEText(body_html, "html", "utf-8"))
    return msg


def _send_smtp(to: str, subject: str, body_html: str) -> None:
    msg = _build_message(to, subject, body_html)
    context = ssl.create_default_context()
    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
            if settings.SMTP_TLS:
                server.starttls(context=context)
            if settings.SMTP_USER:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.EMAIL_FROM, to, msg.as_string())
        logger.info("[EMAIL SMTP] Envoyé à %s | Sujet : %s", to, subject)
    except Exception as e:
        logger.error("[EMAIL SMTP] Échec envoi à %s : %s", to, e)


def _send_mock(to: str, subject: str, body_html: str) -> None:
    logger.info(
        "\n%s\n[EMAIL MOCK]\n  To      : %s\n  Subject : %s\n%s",
        "=" * 60,
        to,
        subject,
        "=" * 60,
    )


def send_email(to: str, subject: str, body_html: str) -> None:
    if settings.EMAIL_MODE == "smtp":
        _send_smtp(to, subject, body_html)
    else:
        _send_mock(to, subject, body_html)


def _get_base_html(content: str) -> str:
    return f"""
    <html>
    <body style="margin: 0; padding: 0; font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f1f5f9; color: #1e293b;">
        <div style="max-width: 600px; margin: 40px auto; background-color: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);">
            <div style="background-color: #0f172a; padding: 40px; text-align: center;">
                <img src="{LOGO_URL}" alt="HORIZON" style="height: 60px; margin-bottom: 16px;">
                <h1 style="color: #60a5fa; margin: 0; font-size: 26px; font-weight: 800; letter-spacing: -0.025em;">HORIZON</h1>
                <p style="color: #94a3b8; margin: 8px 0 0; font-size: 14px; font-weight: 500;">Cloud Académique de l'ENSPY</p>
            </div>
            <div style="padding: 48px; line-height: 1.6;">
                {content}
                <div style="margin-top: 48px; padding-top: 32px; border-top: 1px solid #e2e8f0; font-size: 13px; color: #64748b; text-align: center;">
                    <p style="margin-bottom: 8px;">Ceci est un message automatique du système <b>Horizon</b>.</p>
                    <p style="margin-bottom: 16px;">Merci de ne pas répondre directement à cet e-mail.</p>
                    <div style="font-weight: 600; color: #1e293b;">
                        &copy; {datetime.now().year} Équipe Horizon - École Nationale Supérieure Polytechnique de Yaoundé
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """


# --- Notifications de Comptes ---

def send_account_credentials(to: str, username: str, temp_password: str) -> None:
    content = f"""
        <div style="text-align: center; margin-bottom: 32px;">
            <h2 style="color: #0f172a; font-size: 24px; margin: 0;">Bienvenue sur Horizon !</h2>
            <p style="color: #64748b; margin-top: 8px;">Votre accès est prêt.</p>
        </div>
        <p>Bonjour,</p>
        <p>Votre demande a été approuvée avec succès. Vous pouvez maintenant accéder à vos ressources cloud sur la plateforme <strong>Horizon ENSPY</strong>.</p>
        <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; padding: 24px; border-radius: 12px; margin: 32px 0;">
            <p style="margin: 0 0 12px;"><b>Identifiant :</b> <code style="color: #2563eb; font-size: 16px;">{username}</code></p>
            <p style="margin: 0;"><b>Mot de passe :</b> <code style="color: #2563eb; font-size: 16px;">{temp_password}</code></p>
        </div>
        <div style="background-color: #fff7ed; border-left: 4px solid #f97316; padding: 16px; margin-bottom: 32px; border-radius: 0 8px 8px 0;">
            <p style="margin: 0; color: #9a3412; font-size: 14px;"><b>⚠️ Important :</b> Pour des raisons de sécurité, vous devrez changer ce mot de passe dès votre première connexion.</p>
        </div>
        <div style="text-align: center;">
            <a href="https://horizon.enspy.cm/connexion" style="background-color: #2563eb; color: #ffffff; padding: 14px 40px; text-decoration: none; border-radius: 8px; font-weight: 600; display: inline-block; box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.2);">Accéder à la plateforme</a>
        </div>
    """
    send_email(
        to=to,
        subject="[Horizon ENSPY] Votre accès à la plateforme est prêt",
        body_html=_get_base_html(content),
    )


def send_account_request_received(to: str, first_name: str) -> None:
    content = f"""
        <h2 style="color: #0f172a; font-size: 22px; margin-top: 0;">Accusé de réception</h2>
        <p>Bonjour <b>{first_name}</b>,</p>
        <p>Nous avons bien reçu votre demande de création de compte sur <strong>Horizon</strong>.</p>
        <div style="background-color: #f0f9ff; border-left: 4px solid #0ea5e9; padding: 16px; margin: 24px 0; border-radius: 0 8px 8px 0;">
            <p style="margin: 0; color: #075985;">Un administrateur va examiner votre profil. Vous recevrez une notification par e-mail dès qu'une décision sera prise (généralement sous 24h ouvrées).</p>
        </div>
        <p>Merci de votre patience.</p>
    """
    send_email(
        to=to,
        subject="[Horizon ENSPY] Demande de compte reçue",
        body_html=_get_base_html(content),
    )


def send_account_rejected(to: str, first_name: str, reason: str) -> None:
    content = f"""
        <h2 style="color: #0f172a; font-size: 22px; margin-top: 0;">Statut de votre demande</h2>
        <p>Bonjour <b>{first_name}</b>,</p>
        <p>Nous avons examiné votre demande de compte sur Horizon, mais nous n'avons pas pu l'approuver pour le moment.</p>
        <div style="background-color: #fef2f2; border-left: 4px solid #ef4444; padding: 16px; margin: 24px 0; border-radius: 0 8px 8px 0;">
            <p style="margin: 0; color: #991b1b;"><b>Motif :</b> {reason}</p>
        </div>
        <p>Si vous souhaitez fournir des précisions ou si vous pensez qu'il s'agit d'une erreur, vous pouvez soumettre une nouvelle demande.</p>
    """
    send_email(
        to=to,
        subject="[Horizon ENSPY] Statut de votre demande de compte",
        body_html=_get_base_html(content),
    )


# --- Alertes et Maintenance ---

def send_inactivity_warning(to: str, username: str, days_remaining: int) -> None:
    content = f"""
        <h2 style="color: #0f172a; font-size: 22px; margin-top: 0;">Alerte d'inactivité</h2>
        <p>Bonjour <b>{username}</b>,</p>
        <p>Votre compte Horizon n'a enregistré aucune activité depuis plus de <b>83 jours</b>.</p>
        <p>Conformément à la politique de gestion des ressources, votre accès sera <b>suspendu dans {days_remaining} jours</b>.</p>
        <div style="text-align: center; margin-top: 32px;">
            <a href="https://horizon.enspy.cm/connexion" style="background-color: #2563eb; color: #ffffff; padding: 12px 32px; text-decoration: none; border-radius: 8px; font-weight: 600; display: inline-block;">Se connecter pour rester actif</a>
        </div>
    """
    send_email(
        to=to,
        subject="[Horizon ENSPY] Attention : Votre compte sera bientôt suspendu",
        body_html=_get_base_html(content),
    )


def send_account_suspended(to: str, username: str) -> None:
    content = f"""
        <h2 style="color: #0f172a; font-size: 22px; margin-top: 0;">Compte suspendu</h2>
        <p>Bonjour <b>{username}</b>,</p>
        <p>Votre compte Horizon a été suspendu suite à une inactivité prolongée.</p>
        <div style="background-color: #f1f5f9; padding: 20px; border-radius: 12px; margin: 24px 0;">
            <p style="margin: 0; font-size: 14px; color: #475569;">Vos données sont conservées pendant une période limitée. Pour réactiver votre compte, veuillez contacter le service technique de l'ENSPY.</p>
        </div>
    """
    send_email(
        to=to,
        subject="[Horizon ENSPY] Suspension de votre compte",
        body_html=_get_base_html(content),
    )


def send_vm_expiry_warning(to: str, vm_name: str, minutes_remaining: int) -> None:
    content = f"""
        <h2 style="color: #0f172a; font-size: 22px; margin-top: 0;">Fin de session proche</h2>
        <p>Votre réservation pour la machine <b>{vm_name}</b> expire bientôt.</p>
        <div style="background-color: #fff7ed; padding: 20px; border-radius: 12px; margin: 24px 0; border: 1px solid #ffedd5;">
            <p style="margin: 0; color: #c2410c;">Il reste environ <b>{minutes_remaining} minutes</b> avant l'extinction automatique.</p>
        </div>
        <p>Pensez à sauvegarder vos travaux ou à prolonger la session si nécessaire.</p>
        <div style="text-align: center; margin-top: 32px;">
            <a href="https://horizon.enspy.cm/dashboard" style="background-color: #0f172a; color: #ffffff; padding: 12px 24px; text-decoration: none; border-radius: 8px; font-weight: 600; display: inline-block;">Gérer ma session</a>
        </div>
    """
    send_email(
        to=to,
        subject=f"[Horizon] Fin de session imminente : VM {vm_name}",
        body_html=_get_base_html(content),
    )


def send_vm_force_stopped(to: str, vm_name: str, reason: str) -> None:
    content = f"""
        <h2 style="color: #0f172a; font-size: 22px; margin-top: 0;">Intervention administrative</h2>
        <p>Votre machine virtuelle <b>{vm_name}</b> a été arrêtée par un administrateur système.</p>
        <div style="background-color: #fef2f2; border-left: 4px solid #ef4444; padding: 16px; margin: 24px 0; border-radius: 0 8px 8px 0;">
            <p style="margin: 0; color: #991b1b;"><b>Motif :</b> {reason}</p>
        </div>
    """
    send_email(
        to=to,
        subject=f"[Horizon] Arrêt forcé de la VM {vm_name}",
        body_html=_get_base_html(content),
    )


def send_shared_space_purge_warning(to: str, vm_name: str, hours_remaining: int) -> None:
    content = f"""
        <h2 style="color: #0f172a; font-size: 22px; margin-top: 0;">Nettoyage de l'espace temporaire</h2>
        <p>L'espace de stockage temporaire partagé de votre VM <b>{vm_name}</b> sera purgé dans <b>{hours_remaining} heures</b>.</p>
        <div style="background-color: #f1f5f9; padding: 20px; border-radius: 12px; margin: 24px 0;">
            <p style="margin: 0; font-size: 14px; color: #475569;">N'oubliez pas de sauvegarder vos fichiers importants avant cette échéance.</p>
        </div>
    """
    send_email(
        to=to,
        subject="[Horizon] Rappel : Purge des données temporaires",
        body_html=_get_base_html(content),
    )


# --- Alertes Administrateurs ---

def send_admin_security_alert(admin_emails: list[str], vm_name: str, incident_type: str, details: str) -> None:
    content = f"""
        <div style="background-color: #fee2e2; border: 1px solid #fecaca; padding: 24px; border-radius: 12px;">
            <h2 style="color: #dc2626; margin-top: 0; font-size: 20px;">🚨 ALERTE SÉCURITÉ CRITIQUE</h2>
            <table width="100%" cellpadding="8" style="font-size: 14px; border-collapse: collapse;">
                <tr style="border-bottom: 1px solid #fecaca;"><td><b>Incident</b></td><td>{incident_type}</td></tr>
                <tr style="border-bottom: 1px solid #fecaca;"><td><b>Cible</b></td><td>{vm_name}</td></tr>
                <tr style="border-bottom: 1px solid #fecaca;"><td><b>Détails</b></td><td>{details}</td></tr>
                <tr><td><b>Horodatage</b></td><td>{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</td></tr>
            </table>
        </div>
        <div style="text-align: center; margin-top: 32px;">
            <a href="https://horizon.enspy.cm/admin" style="background-color: #dc2626; color: #ffffff; padding: 12px 32px; text-decoration: none; border-radius: 8px; font-weight: 600; display: inline-block;">Accéder à la console Admin</a>
        </div>
    """
    for email in admin_emails:
        send_email(
            to=email,
            subject=f"⚠️ [Horizon ALERT] {incident_type}",
            body_html=_get_base_html(content),
        )


def send_admin_new_request(admin_emails: list[str], first_name: str, last_name: str, organisation: str) -> None:
    content = f"""
        <h2 style="color: #0f172a; font-size: 20px; margin-top: 0;">Nouvelle demande d'accès</h2>
        <p>Un nouvel utilisateur attend votre validation :</p>
        <div style="background-color: #f8fafc; padding: 20px; border-radius: 12px; border: 1px solid #e2e8f0; margin: 24px 0;">
            <p style="margin: 0 0 8px;"><b>Utilisateur :</b> {last_name} {first_name}</p>
            <p style="margin: 0;"><b>Institution :</b> {organisation.upper()}</p>
        </div>
        <div style="text-align: center;">
            <a href="https://horizon.enspy.cm/admin/demandes" style="background-color: #2563eb; color: #ffffff; padding: 12px 32px; text-decoration: none; border-radius: 8px; font-weight: 600; display: inline-block;">Examiner la demande</a>
        </div>
    """
    for email in admin_emails:
        send_email(
            to=email,
            subject="[Horizon Admin] Nouvelle demande en attente",
            body_html=_get_base_html(content),
        )


def send_login_alert_to_admin(admin_emails: list[str], username: str, ip: str) -> None:
    content = f"""
        <h2 style="color: #dc2626; font-size: 20px; margin-top: 0;">Suspicion de force-brute</h2>
        <p>Le système a détecté de nombreuses tentatives de connexion échouées sur un compte.</p>
        <div style="background-color: #f8fafc; padding: 20px; border-radius: 12px; border: 1px solid #e2e8f0; margin: 24px 0;">
            <p><b>Compte ciblé :</b> {username}</p>
            <p><b>Dernière adresse IP :</b> {ip}</p>
        </div>
        <p>Il est conseillé de vérifier les logs d'audit et éventuellement de bloquer l'IP si l'activité persiste.</p>
    """
    for email in admin_emails:
        send_email(
            to=email,
            subject=f"🚨 [Horizon] Alerte Brute-force : {username}",
            body_html=_get_base_html(content),
        )
