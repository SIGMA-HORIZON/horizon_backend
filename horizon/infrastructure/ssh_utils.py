"""Génération de paires de clés SSH."""

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519


def generate_ssh_key_pair() -> tuple[str, str]:
    """
    Génère une paire de clés Ed25519.
    Retourne (clé_privée_openssh, clé_publique_openssh).
    """
    private_key = ed25519.Ed25519PrivateKey.generate()

    # Format de la clé privée (OpenSSH)
    private_openssh = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.OpenSSH,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")

    # Format de la clé publique (OpenSSH)
    public_openssh = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.OpenSSH,
        format=serialization.PublicFormat.OpenSSH,
    ).decode("utf-8")

    return private_openssh, public_openssh
