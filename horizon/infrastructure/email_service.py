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


def send_account_credentials(to: str, username: str, temp_password: str) -> None:
    send_email(
        to=to,
        subject="[Horizon ENSPY] Votre compte a été créé",
        body_html=f"""
        <p>Bonjour,</p>
        <p>Votre compte sur la plateforme <strong>Horizon ENSPY</strong> a été créé.</p>
        <table border="1" cellpadding="8">
          <tr><td><b>Identifiant</b></td><td>UserName: {username} email: {to}</td></tr>
          <tr><td><b>Mot de passe provisoire</b></td><td><code>{temp_password}</code></td></tr>
        </table>
        <p><strong>Vous devrez changer ce mot de passe à votre première connexion.</strong></p>
        <p>Accédez à la plateforme : <a href="https://horizon.enspy.cm">horizon.enspy.cm</a></p>
        <br><p>— Équipe SIGMA</p>
        """,
    )


def send_account_request_received(to: str, first_name: str) -> None:
    send_email(
        to=to,
        subject="[Horizon ENSPY] Demande de compte reçue",
        body_html=f"""
        <p>Bonjour {first_name},</p>
        <p>Votre demande de création de compte sur <strong>Horizon</strong> a bien été reçue.</p>
        <p>Un administrateur examinera votre demande et vous contactera par e-mail.</p>
        <br><p>— Équipe SIGMA</p>
        """,
    )


def send_account_rejected(to: str, first_name: str, reason: str) -> None:
    send_email(
        to=to,
        subject="[Horizon ENSPY] Demande de compte refusée",
        body_html=f"""
        <p>Bonjour {first_name},</p>
        <p>Votre demande de création de compte sur Horizon n'a pas pu être approuvée.</p>
        <p><b>Motif :</b> {reason}</p>
        <p>Pour toute question, contactez l'équipe SIGMA.</p>
        <br><p>— Équipe SIGMA</p>
        """,
    )


def send_inactivity_warning(to: str, username: str, days_remaining: int) -> None:
    send_email(
        to=to,
        subject="[Horizon ENSPY] Votre compte sera suspendu dans 7 jours",
        body_html=f"""
        <p>Bonjour {username},</p>
        <p>Votre compte Horizon est inactif depuis plus de <b>83 jours</b>.</p>
        <p>Sans connexion dans les <b>{days_remaining} jours</b>, il sera automatiquement suspendu (POL-COMPTE-03).</p>
        <p>Connectez-vous sur <a href="https://horizon.enspy.cm">horizon.enspy.cm</a> pour maintenir votre accès.</p>
        <br><p>— Équipe SIGMA</p>
        """,
    )


def send_account_suspended(to: str, username: str) -> None:
    send_email(
        to=to,
        subject="[Horizon ENSPY] Votre compte a été suspendu",
        body_html=f"""
        <p>Bonjour {username},</p>
        <p>Votre compte Horizon a été suspendu suite à une inactivité prolongée (POL-COMPTE-03).</p>
        <p>Contactez un administrateur pour réactiver votre compte.</p>
        <br><p>— Équipe SIGMA</p>
        """,
    )


def send_vm_expiry_warning(to: str, vm_name: str, minutes_remaining: int) -> None:
    send_email(
        to=to,
        subject=f"[Horizon ENSPY] Votre VM {vm_name} expire dans {minutes_remaining} min",
        body_html=f"""
        <p>Votre VM <b>{vm_name}</b> expirera dans <b>{minutes_remaining} minutes</b>.</p>
        <p>Connectez-vous sur Horizon pour prolonger votre session si des ressources sont disponibles.</p>
        <p>À l'expiration, la VM sera <b>éteinte automatiquement</b>.</p>
        <br><p>— Équipe SIGMA</p>
        """,
    )


def send_vm_force_stopped(to: str, vm_name: str, reason: str) -> None:
    send_email(
        to=to,
        subject=f"[Horizon ENSPY] Votre VM {vm_name} a été arrêtée par un administrateur",
        body_html=f"""
        <p>Votre VM <b>{vm_name}</b> a été arrêtée par un administrateur.</p>
        <p><b>Motif :</b> {reason}</p>
        <p>Pour toute question, contactez l'équipe d'administration.</p>
        <br><p>— Équipe SIGMA</p>
        """,
    )


def send_shared_space_purge_warning(to: str, vm_name: str, hours_remaining: int) -> None:
    send_email(
        to=to,
        subject=f"[Horizon ENSPY] Purge espace partagé VM {vm_name} dans {hours_remaining}h",
        body_html=f"""
        <p>Les données de l'espace partagé de votre VM <b>{vm_name}</b> seront purgées dans <b>{hours_remaining} heure(s)</b>.</p>
        <p>Téléchargez vos fichiers depuis l'interface Horizon avant cette échéance.</p>
        <br><p>— Équipe SIGMA</p>
        """,
    )


def send_admin_security_alert(
    admin_emails: list[str], vm_name: str, incident_type: str, details: str
) -> None:
    for email in admin_emails:
        send_email(
            to=email,
            subject=f"[Horizon ENSPY] ALERTE SÉCURITÉ — {incident_type}",
            body_html=f"""
            <p><b>Alerte de sécurité détectée sur la plateforme Horizon.</b></p>
            <table border="1" cellpadding="8">
              <tr><td><b>Type</b></td><td>{incident_type}</td></tr>
              <tr><td><b>VM concernée</b></td><td>{vm_name}</td></tr>
              <tr><td><b>Détails</b></td><td>{details}</td></tr>
              <tr><td><b>Horodatage</b></td><td>{datetime.utcnow().isoformat()}</td></tr>
            </table>
            <p>Connectez-vous sur Horizon pour investiguer.</p>
            <br><p>— Système de monitoring Horizon</p>
            """,
        )


def send_admin_new_request(
    admin_emails: list[str], first_name: str, last_name: str, organisation: str
) -> None:
    for email in admin_emails:
        send_email(
            to=email,
            subject="[Horizon ENSPY] Nouvelle demande de compte en attente",
            body_html=f"""
            <p>Une nouvelle demande de création de compte a été soumise :</p>
            <table border="1" cellpadding="8">
              <tr><td><b>Nom</b></td><td>{last_name} {first_name}</td></tr>
              <tr><td><b>Organisation</b></td><td>{organisation}</td></tr>
            </table>
            <p>Connectez-vous sur Horizon pour approuver ou refuser cette demande.</p>
            <br><p>— Système Horizon</p>
            """,
        )


def send_login_alert_to_admin(admin_emails: list[str], username: str, ip: str) -> None:
    for email in admin_emails:
        send_email(
            to=email,
            subject=f"[Horizon ENSPY] Alerte brute-force — compte {username}",
            body_html=f"""
            <p>Le compte <b>{username}</b> a atteint {settings.ADMIN_ALERT_ATTEMPTS} tentatives de connexion échouées cumulées.</p>
            <p><b>Dernière IP :</b> {ip}</p>
            <p>Vérifiez s'il s'agit d'une attaque par force brute.</p>
            <br><p>— Système Horizon</p>
            """,
        )
