"""Tests for signer and verifier modules."""

import tempfile
from pathlib import Path

import pytest

from passport.card import AgentCard
from passport.skills import Skill
from passport.signer import Signer, generate_keypair
from passport.verifier import Verifier, verify_card


@pytest.fixture
def sample_card():
    """Create a sample agent card for testing."""
    card = AgentCard.create(name="TestAgent", agent_id="agent-123")
    card.add_skill(Skill(name="Python", confidence=0.9, evidence_count=10))
    return card


@pytest.fixture
def keypair():
    """Generate a temporary keypair for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        private_key_path, public_key_path = generate_keypair(tmpdir)
        yield private_key_path, public_key_path


class TestKeypairGeneration:
    """Tests for keypair generation."""

    def test_generate_keypair_default_location(self):
        """Test generating keypair in default location."""
        import shutil

        with tempfile.TemporaryDirectory() as tmpdir:
            private_key_path, public_key_path = generate_keypair(tmpdir)

            # Verify files exist
            assert Path(private_key_path).exists()
            assert Path(public_key_path).exists()

            # Verify filenames
            assert private_key_path.endswith("agent.key")
            assert public_key_path.endswith("agent.pub")

    def test_generate_keypair_permissions(self):
        """Test private key has restrictive permissions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            private_key_path, _ = generate_keypair(tmpdir)

            # Check permissions (should be 0o600)
            import stat
            file_stat = Path(private_key_path).stat()
            permissions = stat.filemode(file_stat.st_mode)

            # Private key should be read/write for owner only
            assert file_stat.st_mode & 0o777 == 0o600

    def test_generate_keypair_creates_directory(self):
        """Test keypair generation creates output directory if needed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nested_dir = Path(tmpdir) / "nested" / "keys"
            assert not nested_dir.exists()

            private_key_path, public_key_path = generate_keypair(str(nested_dir))

            # Verify directory was created
            assert nested_dir.exists()
            assert Path(private_key_path).exists()
            assert Path(public_key_path).exists()

    def test_keypair_files_are_pem_format(self):
        """Test generated keys are in PEM format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            private_key_path, public_key_path = generate_keypair(tmpdir)

            # Read files
            with open(private_key_path, "r") as f:
                private_pem = f.read()

            with open(public_key_path, "r") as f:
                public_pem = f.read()

            # Verify PEM format
            assert private_pem.startswith("-----BEGIN PRIVATE KEY-----")
            assert private_pem.strip().endswith("-----END PRIVATE KEY-----")
            assert public_pem.startswith("-----BEGIN PUBLIC KEY-----")
            assert public_pem.strip().endswith("-----END PUBLIC KEY-----")


class TestSigner:
    """Tests for Signer class."""

    def test_signer_from_file(self, keypair):
        """Test loading signer from private key file."""
        private_key_path, _ = keypair
        signer = Signer.from_file(private_key_path)

        assert signer is not None
        assert signer.private_key is not None

    def test_signer_sign_card(self, keypair, sample_card):
        """Test signing an agent card."""
        private_key_path, _ = keypair
        signer = Signer.from_file(private_key_path)

        card_dict = sample_card.to_dict()
        signature = signer.sign_card(card_dict)

        # Verify signature is base64 string
        assert isinstance(signature, str)
        assert len(signature) > 0

        # Should be valid base64
        import base64
        try:
            decoded = base64.b64decode(signature)
            assert len(decoded) > 0
        except Exception as e:
            pytest.fail(f"Signature is not valid base64: {e}")

    def test_signer_removes_signature_before_signing(self, keypair, sample_card):
        """Test signer removes existing signature before signing."""
        private_key_path, _ = keypair
        signer = Signer.from_file(private_key_path)

        card_dict = sample_card.to_dict()
        card_dict["signature"] = "old_signature"

        # Should not raise error
        signature = signer.sign_card(card_dict)
        assert signature != "old_signature"

    def test_signer_produces_consistent_signature(self, keypair, sample_card):
        """Test signing same card produces same signature."""
        private_key_path, _ = keypair
        signer = Signer.from_file(private_key_path)

        card_dict = sample_card.to_dict()
        signature1 = signer.sign_card(card_dict)
        signature2 = signer.sign_card(card_dict)

        assert signature1 == signature2

    def test_signer_different_cards_different_signatures(self, keypair):
        """Test signing different cards produces different signatures."""
        private_key_path, _ = keypair
        signer = Signer.from_file(private_key_path)

        card1 = AgentCard.create(name="Agent1", agent_id="agent-1")
        card2 = AgentCard.create(name="Agent2", agent_id="agent-2")

        signature1 = signer.sign_card(card1.to_dict())
        signature2 = signer.sign_card(card2.to_dict())

        assert signature1 != signature2

    def test_signer_get_public_key(self, keypair):
        """Test getting public key from signer."""
        private_key_path, _ = keypair
        signer = Signer.from_file(private_key_path)

        public_key = signer.get_public_key()
        assert public_key is not None

    def test_signer_save_public_key(self, keypair):
        """Test saving public key to file."""
        private_key_path, _ = keypair
        signer = Signer.from_file(private_key_path)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.pub"
            signer.save_public_key(str(output_path))

            # Verify file exists
            assert output_path.exists()

            # Verify PEM format
            with open(output_path, "r") as f:
                pem = f.read()

            assert pem.startswith("-----BEGIN PUBLIC KEY-----")
            assert pem.strip().endswith("-----END PUBLIC KEY-----")

    def test_signer_invalid_key_file_raises_error(self):
        """Test loading non-Ed25519 key raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_key_path = Path(tmpdir) / "fake.key"
            fake_key_path.write_text("not a key")

            with pytest.raises(Exception):
                Signer.from_file(str(fake_key_path))


class TestVerifier:
    """Tests for Verifier class."""

    def test_verifier_from_file(self, keypair):
        """Test loading verifier from public key file."""
        _, public_key_path = keypair
        verifier = Verifier.from_file(public_key_path)

        assert verifier is not None
        assert verifier.public_key is not None

    def test_verifier_verify_valid_signature(self, keypair, sample_card):
        """Test verifying valid signature."""
        private_key_path, public_key_path = keypair

        # Sign card
        signer = Signer.from_file(private_key_path)
        card_dict = sample_card.to_dict()
        signature = signer.sign_card(card_dict)
        card_dict["signature"] = signature

        # Verify
        verifier = Verifier.from_file(public_key_path)
        is_valid = verifier.verify_card(card_dict)

        assert is_valid is True

    def test_verifier_reject_invalid_signature(self, keypair, sample_card):
        """Test rejecting invalid signature."""
        _, public_key_path = keypair

        card_dict = sample_card.to_dict()
        card_dict["signature"] = "invalid_signature_base64=="

        verifier = Verifier.from_file(public_key_path)
        is_valid = verifier.verify_card(card_dict)

        assert is_valid is False

    def test_verifier_reject_tampered_card(self, keypair, sample_card):
        """Test rejecting signature after card is modified."""
        private_key_path, public_key_path = keypair

        # Sign card
        signer = Signer.from_file(private_key_path)
        card_dict = sample_card.to_dict()
        signature = signer.sign_card(card_dict)
        card_dict["signature"] = signature

        # Tamper with card
        card_dict["name"] = "TamperedAgent"

        # Verify
        verifier = Verifier.from_file(public_key_path)
        is_valid = verifier.verify_card(card_dict)

        assert is_valid is False

    def test_verifier_reject_missing_signature(self, keypair, sample_card):
        """Test rejecting card without signature."""
        _, public_key_path = keypair

        card_dict = sample_card.to_dict()
        # No signature field

        verifier = Verifier.from_file(public_key_path)
        is_valid = verifier.verify_card(card_dict)

        assert is_valid is False

    def test_verifier_invalid_key_file_raises_error(self):
        """Test loading non-Ed25519 key raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_key_path = Path(tmpdir) / "fake.pub"
            fake_key_path.write_text("not a key")

            with pytest.raises(Exception):
                Verifier.from_file(str(fake_key_path))


class TestVerifyCardFunction:
    """Tests for verify_card standalone function."""

    def test_verify_card_with_public_key_path(self, keypair, sample_card):
        """Test verify_card function with public key path."""
        private_key_path, public_key_path = keypair

        # Sign card
        signer = Signer.from_file(private_key_path)
        card_dict = sample_card.to_dict()
        signature = signer.sign_card(card_dict)
        card_dict["signature"] = signature

        # Verify using function
        is_valid = verify_card(card_dict, public_key_path=public_key_path)

        assert is_valid is True

    def test_verify_card_with_public_key_object(self, keypair, sample_card):
        """Test verify_card function with public key object."""
        private_key_path, public_key_path = keypair

        # Sign card
        signer = Signer.from_file(private_key_path)
        card_dict = sample_card.to_dict()
        signature = signer.sign_card(card_dict)
        card_dict["signature"] = signature

        # Get public key object
        verifier = Verifier.from_file(public_key_path)
        public_key = verifier.public_key

        # Verify using function
        is_valid = verify_card(card_dict, public_key=public_key)

        assert is_valid is True

    def test_verify_card_no_key_raises_error(self, sample_card):
        """Test verify_card raises error when no key provided."""
        card_dict = sample_card.to_dict()
        card_dict["signature"] = "some_signature"

        with pytest.raises(ValueError, match="Must provide either"):
            verify_card(card_dict)

    def test_verify_card_roundtrip(self, keypair):
        """Test complete sign and verify roundtrip."""
        private_key_path, public_key_path = keypair

        # Create card
        card = AgentCard.create(name="RoundtripAgent", agent_id="agent-roundtrip")
        card.add_skill(Skill(name="Testing", confidence=0.95))

        # Sign
        signer = Signer.from_file(private_key_path)
        card_dict = card.to_dict()
        signature = signer.sign_card(card_dict)
        card.signature = signature

        # Save to dict
        signed_dict = card.to_dict()

        # Verify
        is_valid = verify_card(signed_dict, public_key_path=public_key_path)

        assert is_valid is True
        assert signed_dict["signature"] == signature


class TestSignatureIntegration:
    """Integration tests for signing and verification."""

    def test_end_to_end_signature_workflow(self):
        """Test complete signature workflow from keygen to verify."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 1. Generate keypair
            private_key_path, public_key_path = generate_keypair(tmpdir)

            # 2. Create agent card
            card = AgentCard.create(name="E2EAgent", agent_id="agent-e2e")
            card.add_skill(Skill(name="Integration Testing", confidence=1.0))

            # 3. Sign card
            signer = Signer.from_file(private_key_path)
            card_dict = card.to_dict()
            signature = signer.sign_card(card_dict)
            card.signature = signature

            # 4. Verify signature
            is_valid = verify_card(card.to_dict(), public_key_path=public_key_path)

            assert is_valid is True

    def test_different_keypairs_fail_verification(self):
        """Test signature from one keypair fails with another's public key."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Generate two keypairs
            dir1 = Path(tmpdir) / "keypair1"
            dir2 = Path(tmpdir) / "keypair2"

            private_key_path1, _ = generate_keypair(str(dir1))
            _, public_key_path2 = generate_keypair(str(dir2))

            # Sign with keypair1
            card = AgentCard.create(name="TestAgent")
            signer = Signer.from_file(private_key_path1)
            card_dict = card.to_dict()
            signature = signer.sign_card(card_dict)
            card_dict["signature"] = signature

            # Try to verify with keypair2's public key
            is_valid = verify_card(card_dict, public_key_path=public_key_path2)

            assert is_valid is False
