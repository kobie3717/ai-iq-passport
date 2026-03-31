"""Ed25519 signing for passport verification."""

import base64
import json
import os
from pathlib import Path
from typing import Tuple, Optional

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.hazmat.primitives import serialization


class Signer:
    """Signs agent cards with Ed25519 private key."""

    def __init__(self, private_key: Ed25519PrivateKey):
        """Initialize signer with private key."""
        self.private_key = private_key

    @classmethod
    def from_file(cls, private_key_path: str) -> "Signer":
        """Load signer from private key file.

        Args:
            private_key_path: Path to PEM-encoded private key

        Returns:
            Signer instance
        """
        with open(private_key_path, "rb") as f:
            private_key = serialization.load_pem_private_key(
                f.read(),
                password=None,
            )

        if not isinstance(private_key, Ed25519PrivateKey):
            raise ValueError("Key file is not an Ed25519 private key")

        return cls(private_key)

    def sign_card(self, card_dict: dict) -> str:
        """Sign an agent card dictionary.

        Args:
            card_dict: Agent card as dictionary (without signature field)

        Returns:
            Base64-encoded signature
        """
        # Remove signature field if present
        card_copy = card_dict.copy()
        card_copy.pop("signature", None)

        # Create canonical JSON (sorted keys, no whitespace)
        canonical_json = json.dumps(card_copy, sort_keys=True, separators=(",", ":"))

        # Sign
        signature_bytes = self.private_key.sign(canonical_json.encode("utf-8"))

        # Return base64-encoded signature
        return base64.b64encode(signature_bytes).decode("ascii")

    def get_public_key(self) -> Ed25519PublicKey:
        """Get the public key corresponding to this private key."""
        return self.private_key.public_key()

    def save_public_key(self, output_path: str) -> None:
        """Save public key to PEM file.

        Args:
            output_path: Path where public key will be saved
        """
        public_key = self.get_public_key()
        pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )

        with open(output_path, "wb") as f:
            f.write(pem)


def generate_keypair(output_dir: Optional[str] = None) -> Tuple[str, str]:
    """Generate a new Ed25519 keypair and save to files.

    Args:
        output_dir: Directory to save keys. Defaults to ~/.ai-iq-passport/keys/

    Returns:
        Tuple of (private_key_path, public_key_path)
    """
    if output_dir is None:
        output_dir = os.path.expanduser("~/.ai-iq-passport/keys")

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Generate key
    private_key = Ed25519PrivateKey.generate()

    # Save private key
    private_key_path = output_path / "agent.key"
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    with open(private_key_path, "wb") as f:
        f.write(private_pem)

    # Set restrictive permissions on private key
    os.chmod(private_key_path, 0o600)

    # Save public key
    public_key_path = output_path / "agent.pub"
    public_key = private_key.public_key()
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    with open(public_key_path, "wb") as f:
        f.write(public_pem)

    return str(private_key_path), str(public_key_path)
