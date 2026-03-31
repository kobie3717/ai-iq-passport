"""Verify passport card signatures."""

import base64
import json
from typing import Optional

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidSignature


class Verifier:
    """Verifies agent card signatures."""

    def __init__(self, public_key: Ed25519PublicKey):
        """Initialize verifier with public key."""
        self.public_key = public_key

    @classmethod
    def from_file(cls, public_key_path: str) -> "Verifier":
        """Load verifier from public key file.

        Args:
            public_key_path: Path to PEM-encoded public key

        Returns:
            Verifier instance
        """
        with open(public_key_path, "rb") as f:
            public_key = serialization.load_pem_public_key(f.read())

        if not isinstance(public_key, Ed25519PublicKey):
            raise ValueError("Key file is not an Ed25519 public key")

        return cls(public_key)

    def verify_card(self, card_dict: dict) -> bool:
        """Verify an agent card signature.

        Args:
            card_dict: Agent card dictionary with signature field

        Returns:
            True if signature is valid, False otherwise
        """
        signature_b64 = card_dict.get("signature")
        if not signature_b64:
            return False

        # Remove signature for verification
        card_copy = card_dict.copy()
        card_copy.pop("signature")

        # Create canonical JSON
        canonical_json = json.dumps(card_copy, sort_keys=True, separators=(",", ":"))

        try:
            # Decode signature
            signature_bytes = base64.b64decode(signature_b64)

            # Verify
            self.public_key.verify(signature_bytes, canonical_json.encode("utf-8"))
            return True

        except (InvalidSignature, Exception):
            return False


def verify_card(
    card_dict: dict,
    public_key_path: Optional[str] = None,
    public_key: Optional[Ed25519PublicKey] = None,
) -> bool:
    """Verify an agent card signature.

    Args:
        card_dict: Agent card dictionary with signature
        public_key_path: Path to public key file (PEM)
        public_key: Ed25519PublicKey object (alternative to path)

    Returns:
        True if signature is valid

    Raises:
        ValueError: If neither public_key_path nor public_key is provided
    """
    if public_key:
        verifier = Verifier(public_key)
    elif public_key_path:
        verifier = Verifier.from_file(public_key_path)
    else:
        raise ValueError("Must provide either public_key_path or public_key")

    return verifier.verify_card(card_dict)
