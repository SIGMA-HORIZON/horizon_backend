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
    <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f8fafc; color: #1e293b;">
        <div style="max-width: 600px; margin: 20px auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);">
            <div style="background-color: #0f172a; padding: 32px; text-align: center;">
                <h1 style="color: #60a5fa; margin: 0; font-size: 24px; letter-spacing: 1px;">SIGMA HORIZON</h1>
                <p style="color: #94a3b8; margin: 8px 0 0; font-size: 14px;">Cloud Académique ENSPY</p>
            </div>
            <div style="padding: 40px;">
                {content}
                <div style="margin-top: 40px; padding-top: 24px; border-top: 1px solid #e2e8f0; font-size: 12px; color: #64748b; text-align: center;">
                    Ceci est un message automatique du système Horizon. Merci de ne pas répondre directement.<br>
                    &copy; {datetime.now().year} Équipe SIGMA - École Nationale Supérieure Polytechnique de Yaoundé.
                </div>
            </div>
        </div>
    </body>
    </html>
    """

def send_account_credentials(to: str, username: str, temp_password: str) -> None:
    content = f"""
        <h2 style="color: #1e293b; margin-top: 0;">Bienvenue sur Horizon</h2>
        <p>Bonjour,</p>
        <p>Votre demande a été approuvée ! Votre compte sur la plateforme <strong>Horizon ENSPY</strong> est désormais prêt.</p>
        <div style="background-color: #f1f5f9; padding: 24px; border-radius: 8px; margin: 24px 0;">
            <p style="margin: 0 0 12px;"><b>Identifiant :</b> <span style="font-family: monospace; color: #2563eb;">{username}</span></p>
            <p style="margin: 0;"><b>Mot de passe provisoire :</b> <span style="font-family: monospace; color: #2563eb;">{temp_password}</span></p>
        </div>
        <p style="color: #ef4444; font-weight: 600;">⚠️ Vous devrez impérativement changer ce mot de passe lors de votre première connexion.</p>
        <div style="text-align: center; margin-top: 32px;">
            <a href="http://localhost:3010/connexion" style="background-color: #2563eb; color: #ffffff; padding: 12px 32px; text-decoration: none; border-radius: 6px; font-weight: 600; display: inline-block;">Accéder à la plateforme</a>
        </div>
    """
    send_email(
        to=to,
        subject="[Horizon ENSPY] Votre accès à la plateforme est prêt",
        body_html=_get_base_html(content),
    )


def send_account_request_received(to: str, first_name: str) -> None:
    content = f"""
        <h2 style="color: #1e293b; margin-top: 0;">Accusé de réception</h2>
        <p>Bonjour {first_name},</p>
        <p>Votre demande de création de compte sur <strong>Horizon</strong> a bien été enregistrée dans notre système.</p>
        <p>Un administrateur va examiner votre profil et la justification fournie. Vous recevrez une notification par e-mail dès qu'une décision sera prise.</p>
        <div style="text-align: center; margin-top: 32px;">
            <a href="http://localhost:3010" style="color: #2563eb; font-weight: 600; text-decoration: none;">Visiter le site Horizon</a>
        </div>
    """
    send_email(
        to=to,
        subject="[Horizon ENSPY] Demande de compte reçue",
        body_html=_get_base_html(content),
    )


def send_account_rejected(to: str, first_name: str, reason: str) -> None:
    content = f"""
        <h2 style="color: #1e293b; margin-top: 0;">Information sur votre demande</h2>
        <p>Bonjour {first_name},</p>
        <p>Nous avons examiné votre demande de création de compte sur Horizon, mais nous n'avons pas pu l'approuver pour le moment.</p>
        <div style="background-color: #fef2f2; border-left: 4px solid #ef4444; padding: 16px; margin: 24px 0;">
            <p style="margin: 0; color: #991b1b;"><b>Motif du refus :</b> {reason}</p>
        </div>
        <p>Si vous pensez qu'il s'agit d'une erreur ou si vous souhaitez fournir des précisions, vous pouvez soumettre une nouvelle demande.</p>
    """
    send_email(
        to=to,
        subject="[Horizon ENSPY] Statut de votre demande de compte",
        body_html=_get_base_html(content),
    )


def send_inactivity_warning(to: str, username: str, days_remaining: int) -> None:
    content = f"""
        <h2 style="color: #1e293b; margin-top: 0;">Alerte d'inactivité</h2>
        <p>Bonjour {username},</p>
        <p>Votre compte Horizon est inactif depuis plus de <b>83 jours</b>.</p>
        <p>Conformément à notre politique de gestion des ressources (POL-COMPTE-03), votre accès sera <b>suspendu dans {days_remaining} jours</b> si aucune connexion n'est détectée.</p>
        <div style="text-align: center; margin-top: 32px;">
            <a href="http://localhost:3010/connexion" style="background-color: #2563eb; color: #ffffff; padding: 12px 32px; text-decoration: none; border-radius: 6px; font-weight: 600; display: inline-block;">Se connecter maintenant</a>
        </div>
    """
    send_email(
        to=to,
        subject="[Horizon ENSPY] Attention : Votre compte sera bientôt suspendu",
        body_html=_get_base_html(content),
    )


def send_account_suspended(to: str, username: str) -> None:
    content = f"""
        <h2 style="color: #1e293b; margin-top: 0;">Compte suspendu</h2>
        <p>Bonjour {username},</p>
        <p>Votre compte Horizon a été suspendu suite à une inactivité prolongée (POL-COMPTE-03).</p>
        <p>Vos données sont conservées pendant une période limitée. Pour réactiver votre compte, veuillez contacter le service technique de l'ENSPY.</p>
    """
    send_email(
        to=to,
        subject="[Horizon ENSPY] Suspension de votre compte",
        body_html=_get_base_html(content),
    )


def send_vm_expiry_warning(to: str, vm_name: str, minutes_remaining: int) -> None:
    content = f"""
        <h2 style="color: #1e293b; margin-top: 0;">Expiration de session VM</h2>
        <p>Votre machine virtuelle <b>{vm_name}</b> arrive au terme de son temps de réservation.</p>
        <p>Il reste environ <b>{minutes_remaining} minutes</b> avant que la machine ne soit automatiquement éteinte.</p>
        <p>Connectez-vous sur le dashboard pour prolonger votre session si des ressources sont encore disponibles.</p>
        <div style="text-align: center; margin-top: 32px;">
            <a href="http://localhost:3010/dashboard" style="background-color: #2563eb; color: #ffffff; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: 600; display: inline-block;">Gérer mes VMs</a>
        </div>
    """
    send_email(
        to=to,
        subject=f"[Horizon ENSPY] Fin de session imminente : VM {vm_name}",
        body_html=_get_base_html(content),
    )


def send_vm_force_stopped(to: str, vm_name: str, reason: str) -> None:
    content = f"""
        <h2 style="color: #1e293b; margin-top: 0;">Intervention administrative</h2>
        <p>Votre machine virtuelle <b>{vm_name}</b> a été arrêtée par un administrateur système.</p>
        <div style="background-color: #fef2f2; border-left: 4px solid #ef4444; padding: 16px; margin: 24px 0;">
            <p style="margin: 0; color: #991b1b;"><b>Motif :</b> {reason}</p>
        </div>
    """
    send_email(
        to=to,
        subject=f"[Horizon ENSPY] Arrêt forcé de la VM {vm_name}",
        body_html=_get_base_html(content),
    )


def send_shared_space_purge_warning(to: str, vm_name: str, hours_remaining: int) -> None:
    content = f"""
        <h2 style="color: #1e293b; margin-top: 0;">Nettoyage de l'espace temporaire</h2>
        <p>L'espace de stockage temporaire partagé de votre VM <b>{vm_name}</b> sera purgé dans <b>{hours_remaining} heures</b>.</p>
        <p>N'oubliez pas de sauvegarder vos fichiers importants avant cette échéance.</p>
    """
    send_email(
        to=to,
        subject="[Horizon ENSPY] Rappel : Purge des données temporaires",
        body_html=_get_base_html(content),
    )


def send_admin_security_alert(
    admin_emails: list[str], vm_name: str, incident_type: str, details: str
) -> None:
    content = f"""
        <h2 style="color: #ef4444; margin-top: 0;">ALERTE SÉCURITÉ CRITIQUE</h2>
        <p>Une anomalie de sécurité a été détectée sur la plateforme.</p>
        <div style="background-color: #f8fafc; padding: 24px; border-radius: 8px; border: 1px solid #e2e8f0; margin: 24px 0;">
            <table width="100%" cellpadding="8">
                <tr><td><b>Type d'incident</b></td><td>{incident_type}</td></tr>
                <tr><td><b>VM concernée</b></td><td>{vm_name}</td></tr>
                <tr><td><b>Détails</b></td><td>{details}</td></tr>
                <tr><td><b>Date/Heure</b></td><td>{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</td></tr>
            </table>
        </div>
        <div style="text-align: center; margin-top: 32px;">
            <a href="http://localhost:3010/admin" style="background-color: #dc2626; color: #ffffff; padding: 12px 32px; text-decoration: none; border-radius: 6px; font-weight: 600; display: inline-block;">Investiguer dans l'Admin</a>
        </div>
    """
    for email in admin_emails:
        send_email(
            to=email,
            subject=f"⚠️ [Horizon ALERT] {incident_type}",
            body_html=_get_base_html(content),
        )


def send_admin_new_request(
    admin_emails: list[str], first_name: str, last_name: str, organisation: str
) -> None:
    content = f"""
        <h2 style="color: #1e293b; margin-top: 0;">Nouvelle demande d'accès</h2>
        <p>Un utilisateur a soumis une nouvelle demande de création de compte qui nécessite votre validation.</p>
        <div style="background-color: #f1f5f9; padding: 20px; border-radius: 8px; margin: 24px 0;">
            <p style="margin: 0 0 8px;"><b>Nom :</b> {last_name} {first_name}</p>
            <p style="margin: 0;"><b>Institution :</b> {organisation.upper()}</p>
        </div>
        <div style="text-align: center; margin-top: 32px;">
            <a href="http://localhost:3010/admin/demandes" style="background-color: #2563eb; color: #ffffff; padding: 12px 32px; text-decoration: none; border-radius: 6px; font-weight: 600; display: inline-block;">Gérer les demandes</a>
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
        <h2 style="color: #ef4444; margin-top: 0;">Suspicion de force-brute</h2>
        <p>Le système a détecté de nombreuses tentatives de connexion échouées sur un compte.</p>
        <div style="background-color: #f8fafc; padding: 20px; border-radius: 8px; border: 1px solid #e2e8f0; margin: 24px 0;">
            <p><b>Compte ciblé :</b> {username}</p>
            <p><b>Dernière adresse IP :</b> {ip}</p>
        </div>
        <p>Il est conseillé de vérifier les logs d'audit et éventuellement de bloquer temporairement l'IP concernée si l'activité persiste.</p>
    """
    for email in admin_emails:
        send_email(
            to=email,
            subject=f"🚨 [Horizon] Alerte Brute-force : {username}",
            body_html=_get_base_html(content),
        )
