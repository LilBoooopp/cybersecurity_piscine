#!/usr/bin/python3

import hmac
import hashlib
import struct
import time
import sys

def store_key(path):
    try:
        with open(path, 'r') as f:
            key = f.read().strip()
    except FileNotFoundError:
        print(f"ft_otp: error: file not found: {path}")
        sys.exit(1)

    if len(key) < 64:
        print("ft_otp: error: key must be 64 hexadecimal characters.")
        sys.exit(1)
    if not all(c in "0123456789abcdefABCDEF" for c in key):
        print("ft_otp: error: key must be 64 hexadecimal characters.")
        sys.exit(1)

    encryption_key = b"ft_otp_secret_42"
    key_bytes = key.encode()
    encrypted = bytes([b ^ encryption_key[i % len(encryption_key)]
                    for i, b in enumerate(key_bytes)])

    with open("ft_otp.key", 'wb') as f:
        f.write(encrypted)

    print("Key was successfully saved in ft_otp.key.")

def gen_key(path):
    encryption_key = b"ft_otp_secret_42"
    try:
        with open(path, 'rb') as f:
            encrypted = f.read()
    except FileNotFoundError:
        print(f"ft_otp: error: file not found: {path}")
        sys.exit(1)

    key = bytes([b ^ encryption_key[i % len(encryption_key)]
                for i, b in enumerate(encrypted)]).decode()

    counter = int(time.time()) // 30
    counter_bytes = struct.pack(">Q", counter)
    key_bytes = bytes.fromhex(key)
    h = hmac.new(key_bytes, counter_bytes, hashlib.sha1)
    hash_bytes = h.digest()
    
    offset = hash_bytes[19] & 0x0F
    b = struct.unpack(">I", hash_bytes[offset:offset+4])[0]
    number = b & 0x7FFFFFFF
    code = number % 1_000_000
    print(str(code).zfill(6))

def main(args):
    if len(args) != 3:
        print("Usage: ft_otp -g <keyfile> || ft_otp -k <keyfile>")
        sys.exit(1)
    elif (args[1] == "-g"):
        store_key(args[2])
    elif (args[1] == "-k"):
        gen_key(args[2])
    else:
        print("ft_otp: error: unknown flag")
        sys.exit(1)

if __name__ == "__main__":
    main(sys.argv)
