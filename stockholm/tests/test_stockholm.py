import pytest
import os
import sys
from pathlib import Path
from unittest.mock import patch
from cryptography.exceptions import InvalidTag

# ─── make sure the module is importable ──────────────────────────────────────

sys.path.insert(0, str(Path(__file__).parent.parent))
import stockholm

# ═══════════════════════════════════════════════════════════════════════════════
# fixtures
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def infection_dir(tmp_path):
    """Create a temporary ~/infection directory and patch HOME."""
    d = tmp_path / "infection"
    d.mkdir()
    with patch.dict(os.environ, {"HOME": str(tmp_path)}):
        yield d

@pytest.fixture
def extensions_file(tmp_path):
    """Write a minimal extensions file and return its path."""
    f = tmp_path / "wannacry_extensions.txt"
    f.write_text(".txt\n.jpg\n.pdf\n.docx\n")
    return f

@pytest.fixture
def sample_files(infection_dir):
    """Populate infection_dir with a handful of files."""
    files = {
        "note.txt":    b"hello world",
        "image.jpg":   b"\xff\xd8\xff" + b"fake jpeg data",
        "archive.zip": b"PK\x03\x04fake zip",   # not in extensions
        "doc.docx":    b"fake docx content",
    }
    for name, content in files.items():
        (infection_dir / name).write_bytes(content)
    return files

PASSWORD = "mysecretpassword"   # exactly 16 chars

# ═══════════════════════════════════════════════════════════════════════════════
# crypto primitives
# ═══════════════════════════════════════════════════════════════════════════════

class TestCryptoPrimitives:

    def test_encrypt_decrypt_roundtrip(self):
        plaintext = b"sensitive data 1234"
        blob = stockholm.encrypt_bytes(plaintext, PASSWORD)
        assert stockholm.decrypt_bytes(blob, PASSWORD) == plaintext

    def test_encrypt_produces_different_output_each_call(self):
        """Random salt+nonce means two encryptions of the same plaintext differ."""
        pt = b"same content"
        assert stockholm.encrypt_bytes(pt, PASSWORD) != stockholm.encrypt_bytes(pt, PASSWORD)

    def test_decrypt_wrong_password_returns_none(self):
        blob = stockholm.encrypt_bytes(b"secret", PASSWORD)
        assert stockholm.decrypt_bytes(blob, "wrongpassword!!") is None

    def test_decrypt_truncated_data_returns_none(self):
        blob = stockholm.encrypt_bytes(b"secret", PASSWORD)
        assert stockholm.decrypt_bytes(blob[:10], PASSWORD) is None

    def test_decrypt_empty_returns_none(self):
        assert stockholm.decrypt_bytes(b"", PASSWORD) is None

    def test_decrypt_flipped_ciphertext_bit_returns_none(self):
        """Tampered ciphertext must fail GCM tag verification."""
        blob = bytearray(stockholm.encrypt_bytes(b"tamper me", PASSWORD))
        blob[-1] ^= 0xFF   # flip last byte (inside the GCM tag)
        assert stockholm.decrypt_bytes(bytes(blob), PASSWORD) is None

    def test_encrypt_output_length(self):
        """Output must be at least HEADER_SIZE + 16 (GCM tag) bytes larger than input."""
        pt = b"x" * 100
        blob = stockholm.encrypt_bytes(pt, PASSWORD)
        assert len(blob) == stockholm.HEADER_SIZE + len(pt) + 16

    def test_roundtrip_empty_file(self):
        blob = stockholm.encrypt_bytes(b"", PASSWORD)
        assert stockholm.decrypt_bytes(blob, PASSWORD) == b""

    def test_roundtrip_large_file(self):
        pt = os.urandom(10 * 1024 * 1024)   # 10 MB
        blob = stockholm.encrypt_bytes(pt, PASSWORD)
        assert stockholm.decrypt_bytes(blob, PASSWORD) == pt

    def test_roundtrip_binary_data(self):
        pt = bytes(range(256)) * 100
        blob = stockholm.encrypt_bytes(pt, PASSWORD)
        assert stockholm.decrypt_bytes(blob, PASSWORD) == pt

    def test_derive_key_deterministic(self):
        """Same password + salt must always produce the same key."""
        salt = b"\x00" * stockholm.SALT_SIZE
        k1 = stockholm.derive_key(PASSWORD, salt)
        k2 = stockholm.derive_key(PASSWORD, salt)
        assert k1 == k2

    def test_derive_key_length(self):
        salt = os.urandom(stockholm.SALT_SIZE)
        assert len(stockholm.derive_key(PASSWORD, salt)) == stockholm.KEY_SIZE

    def test_derive_key_different_salts(self):
        s1, s2 = os.urandom(16), os.urandom(16)
        assert stockholm.derive_key(PASSWORD, s1) != stockholm.derive_key(PASSWORD, s2)

# ═══════════════════════════════════════════════════════════════════════════════
# extensions loader
# ═══════════════════════════════════════════════════════════════════════════════

class TestLoadExtensions:

    def test_loads_dot_prefixed(self, tmp_path):
        f = tmp_path / "ext.txt"
        f.write_text(".txt\n.jpg\n")
        assert stockholm.load_extensions(f) == {".txt", ".jpg"}

    def test_adds_dot_if_missing(self, tmp_path):
        f = tmp_path / "ext.txt"
        f.write_text("txt\njpg\n")
        assert stockholm.load_extensions(f) == {".txt", ".jpg"}

    def test_normalises_to_lowercase(self, tmp_path):
        f = tmp_path / "ext.txt"
        f.write_text(".TXT\n.JPG\n")
        assert stockholm.load_extensions(f) == {".txt", ".jpg"}

    def test_skips_blank_lines(self, tmp_path):
        f = tmp_path / "ext.txt"
        f.write_text(".txt\n\n  \n.jpg\n")
        assert stockholm.load_extensions(f) == {".txt", ".jpg"}

    def test_missing_file_exits(self, tmp_path):
        with pytest.raises(SystemExit):
            stockholm.load_extensions(tmp_path / "nonexistent.txt")

# ═══════════════════════════════════════════════════════════════════════════════
# should_process
# ═══════════════════════════════════════════════════════════════════════════════

class TestShouldProcess:

    EXTS = {".txt", ".jpg", ".docx"}

    def test_encrypt_targets_matching_extension(self, tmp_path):
        assert stockholm.should_process(tmp_path / "a.txt", False, self.EXTS)

    def test_encrypt_skips_non_matching_extension(self, tmp_path):
        assert not stockholm.should_process(tmp_path / "a.zip", False, self.EXTS)

    def test_encrypt_skips_already_encrypted(self, tmp_path):
        assert not stockholm.should_process(tmp_path / "a.txt.ft", False, self.EXTS)

    def test_decrypt_targets_ft_files(self, tmp_path):
        assert stockholm.should_process(tmp_path / "a.txt.ft", True, self.EXTS)

    def test_decrypt_skips_non_ft_files(self, tmp_path):
        assert not stockholm.should_process(tmp_path / "a.txt", True, self.EXTS)

    def test_encrypt_case_insensitive_extension(self, tmp_path):
        assert stockholm.should_process(tmp_path / "a.TXT", False, self.EXTS)

# ═══════════════════════════════════════════════════════════════════════════════
# collect_targets
# ═══════════════════════════════════════════════════════════════════════════════

class TestCollectTargets:

    EXTS = {".txt", ".jpg", ".docx"}

    def test_finds_matching_files(self, infection_dir, sample_files):
        targets = stockholm.collect_targets(infection_dir, False, self.EXTS)
        names = {t.name for t in targets}
        assert names == {"note.txt", "image.jpg", "doc.docx"}

    def test_skips_non_matching_extensions(self, infection_dir, sample_files):
        targets = stockholm.collect_targets(infection_dir, False, self.EXTS)
        assert not any(t.name == "archive.zip" for t in targets)

    def test_decrypt_mode_finds_ft_files(self, infection_dir):
        (infection_dir / "note.txt.ft").write_bytes(b"blob")
        (infection_dir / "image.jpg.ft").write_bytes(b"blob")
        (infection_dir / "note.txt").write_bytes(b"plain")   # should be ignored
        targets = stockholm.collect_targets(infection_dir, True, self.EXTS)
        names = {t.name for t in targets}
        assert names == {"note.txt.ft", "image.jpg.ft"}

    def test_recurses_into_subdirectories(self, infection_dir):
        sub = infection_dir / "subdir"
        sub.mkdir()
        (sub / "deep.txt").write_bytes(b"nested")
        targets = stockholm.collect_targets(infection_dir, False, self.EXTS)
        assert any(t.name == "deep.txt" for t in targets)

    def test_empty_dir_returns_empty_list(self, infection_dir):
        assert stockholm.collect_targets(infection_dir, False, self.EXTS) == []

# ═══════════════════════════════════════════════════════════════════════════════
# encrypt_file / decrypt_file
# ═══════════════════════════════════════════════════════════════════════════════

class TestEncryptFile:

    def test_creates_ft_file(self, infection_dir):
        f = infection_dir / "note.txt"
        f.write_bytes(b"hello")
        stockholm.encrypt_file(f, PASSWORD, silent=True)
        assert (infection_dir / "note.txt.ft").exists()

    def test_removes_original(self, infection_dir):
        f = infection_dir / "note.txt"
        f.write_bytes(b"hello")
        stockholm.encrypt_file(f, PASSWORD, silent=True)
        assert not f.exists()

    def test_encrypted_content_differs_from_plaintext(self, infection_dir):
        f = infection_dir / "note.txt"
        f.write_bytes(b"hello world")
        stockholm.encrypt_file(f, PASSWORD, silent=True)
        assert (infection_dir / "note.txt.ft").read_bytes() != b"hello world"

    def test_silent_produces_no_stdout(self, infection_dir, capsys):
        f = infection_dir / "note.txt"
        f.write_bytes(b"hi")
        stockholm.encrypt_file(f, PASSWORD, silent=True)
        assert capsys.readouterr().out == ""

    def test_non_silent_prints_filename(self, infection_dir, capsys):
        f = infection_dir / "note.txt"
        f.write_bytes(b"hi")
        stockholm.encrypt_file(f, PASSWORD, silent=False)
        out = capsys.readouterr().out
        assert "note.txt" in out

    def test_unreadable_file_prints_warning(self, infection_dir, capsys):
        f = infection_dir / "note.txt"
        f.write_bytes(b"hi")
        f.chmod(0o000)
        stockholm.encrypt_file(f, PASSWORD, silent=True)
        assert "warning" in capsys.readouterr().err
        f.chmod(0o644)   # restore so tmp_path cleanup works

    def test_missing_file_prints_warning(self, infection_dir, capsys):
        stockholm.encrypt_file(infection_dir / "ghost.txt", PASSWORD, silent=True)
        assert "warning" in capsys.readouterr().err


class TestDecryptFile:

    def _make_encrypted(self, infection_dir, name, content):
        """Helper: encrypt content and write the .ft file directly."""
        blob = stockholm.encrypt_bytes(content, PASSWORD)
        ft = infection_dir / (name + ".ft")
        ft.write_bytes(blob)
        return ft

    def test_restores_original_file(self, infection_dir):
        ft = self._make_encrypted(infection_dir, "note.txt", b"hello world")
        stockholm.decrypt_file(ft, PASSWORD, silent=True)
        assert (infection_dir / "note.txt").read_bytes() == b"hello world"

    def test_removes_ft_file(self, infection_dir):
        ft = self._make_encrypted(infection_dir, "note.txt", b"hello")
        stockholm.decrypt_file(ft, PASSWORD, silent=True)
        assert not ft.exists()

    def test_wrong_key_leaves_ft_intact(self, infection_dir, capsys):
        ft = self._make_encrypted(infection_dir, "note.txt", b"secret")
        stockholm.decrypt_file(ft, "wrongpassword!!!", silent=True)
        assert ft.exists()
        assert "error" in capsys.readouterr().err

    def test_corrupt_file_leaves_ft_intact(self, infection_dir, capsys):
        ft = infection_dir / "note.txt.ft"
        ft.write_bytes(b"this is not a valid encrypted blob at all")
        stockholm.decrypt_file(ft, PASSWORD, silent=True)
        assert ft.exists()

    def test_silent_produces_no_stdout(self, infection_dir, capsys):
        ft = self._make_encrypted(infection_dir, "note.txt", b"hi")
        stockholm.decrypt_file(ft, PASSWORD, silent=True)
        assert capsys.readouterr().out == ""

    def test_non_silent_prints_filename(self, infection_dir, capsys):
        ft = self._make_encrypted(infection_dir, "note.txt", b"hi")
        stockholm.decrypt_file(ft, PASSWORD, silent=False)
        assert "note.txt" in capsys.readouterr().out

    def test_extension_preserved_after_roundtrip(self, infection_dir):
        """photo.jpg.ft must decrypt back to photo.jpg, not photo."""
        blob = stockholm.encrypt_bytes(b"jpeg data", PASSWORD)
        ft = infection_dir / "photo.jpg.ft"
        ft.write_bytes(blob)
        stockholm.decrypt_file(ft, PASSWORD, silent=True)
        assert (infection_dir / "photo.jpg").exists()
        assert not (infection_dir / "photo").exists()

# ═══════════════════════════════════════════════════════════════════════════════
# full encrypt → decrypt roundtrip (integration)
# ═══════════════════════════════════════════════════════════════════════════════

class TestFullRoundtrip:

    EXTS = {".txt", ".jpg", ".docx"}

    def test_roundtrip_single_file(self, infection_dir):
        f = infection_dir / "note.txt"
        f.write_bytes(b"important data")

        stockholm.encrypt_file(f, PASSWORD, silent=True)
        assert not f.exists()
        assert (infection_dir / "note.txt.ft").exists()

        stockholm.decrypt_file(infection_dir / "note.txt.ft", PASSWORD, silent=True)
        assert f.read_bytes() == b"important data"

    def test_roundtrip_all_sample_files(self, infection_dir, sample_files):
        originals = {
            name: content
            for name, content in sample_files.items()
            if Path(name).suffix.lower() in self.EXTS
        }

        # encrypt pass
        for name in originals:
            stockholm.encrypt_file(infection_dir / name, PASSWORD, silent=True)

        # all originals gone, .ft files present
        for name in originals:
            assert not (infection_dir / name).exists()
            assert (infection_dir / (name + ".ft")).exists()

        # decrypt pass
        for name in originals:
            stockholm.decrypt_file(infection_dir / (name + ".ft"), PASSWORD, silent=True)

        # all originals restored with correct content
        for name, content in originals.items():
            assert (infection_dir / name).read_bytes() == content

    def test_zip_file_untouched_throughout(self, infection_dir, sample_files):
        """Files not in the extension list must never be modified."""
        zip_path = infection_dir / "archive.zip"
        original_content = zip_path.read_bytes()

        targets = stockholm.collect_targets(infection_dir, False, self.EXTS)
        for t in targets:
            stockholm.encrypt_file(t, PASSWORD, silent=True)

        assert zip_path.read_bytes() == original_content

    def test_double_encrypt_skipped_by_collect(self, infection_dir):
        """Running encrypt twice must not re-encrypt already-.ft files."""
        f = infection_dir / "note.txt"
        f.write_bytes(b"data")

        stockholm.encrypt_file(f, PASSWORD, silent=True)
        ft = infection_dir / "note.txt.ft"
        blob_after_first = ft.read_bytes()

        # second collect should return zero targets (no .txt left, .ft excluded)
        targets = stockholm.collect_targets(infection_dir, False, self.EXTS)
        assert targets == []
        assert ft.read_bytes() == blob_after_first

    def test_wrong_key_does_not_corrupt(self, infection_dir):
        f = infection_dir / "note.txt"
        f.write_bytes(b"do not corrupt me")
        stockholm.encrypt_file(f, PASSWORD, silent=True)

        ft = infection_dir / "note.txt.ft"
        blob_before = ft.read_bytes()
        stockholm.decrypt_file(ft, "wrongpassword!!!", silent=True)

        # .ft still intact and unchanged
        assert ft.read_bytes() == blob_before
        assert not (infection_dir / "note.txt").exists()

# ═══════════════════════════════════════════════════════════════════════════════
# argument parsing
# ═══════════════════════════════════════════════════════════════════════════════

class TestArgParsing:

    def test_key_mode(self):
        args = stockholm.parse_args(["-k", "mysecretpassword"])
        assert args.key == "mysecretpassword"
        assert args.reverse is None

    def test_reverse_mode(self):
        args = stockholm.parse_args(["-r", "mysecretpassword"])
        assert args.reverse == "mysecretpassword"
        assert args.key is None

    def test_silent_flag(self):
        args = stockholm.parse_args(["-k", "mysecretpassword", "-s"])
        assert args.silent is True

    def test_silent_default_false(self):
        args = stockholm.parse_args(["-k", "mysecretpassword"])
        assert args.silent is False

    def test_short_key_rejected(self):
        with pytest.raises(SystemExit):
            stockholm.parse_args(["-k", "tooshort"])

    def test_key_and_reverse_mutually_exclusive(self):
        with pytest.raises(SystemExit):
            stockholm.parse_args(["-k", "mysecretpassword", "-r", "mysecretpassword"])

    def test_no_mode_exits(self):
        with pytest.raises(SystemExit):
            stockholm.parse_args([])

    def test_version_exits(self):
        with pytest.raises(SystemExit):
            stockholm.parse_args(["--version"])

    def test_exactly_16_char_key_accepted(self):
        args = stockholm.parse_args(["-k", "a" * 16])
        assert args.key == "a" * 16

    def test_long_key_accepted(self):
        args = stockholm.parse_args(["-k", "a" * 64])
        assert args.key == "a" * 64
