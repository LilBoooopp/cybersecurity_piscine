#!/bin/python3

import hmac
import hashlib
import struct
import time
import sys

def store_key(path):
    with open(path, 'r') as f:
        key = f.read().strip()

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

def gen_key(key):
    pass

def main(args):
    if len(args) != 3:
        print("Usage: ft_otp -g <keyfile> | ft_otp -k <keyfile>")
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
