#!/usr/bin/python3
from hashlib import sha3_256
import sys


if len(sys.argv) < 2:
    print("Usage: python3 pwdcrypt.py <password> [<salt>]")
    exit(1)

if len(sys.argv) >= 3:
    print(sha3_256((sys.argv[2] + sys.argv[1]).encode()).hexdigest())
    exit(0)

from config import API_SALT
print(sha3_256((API_SALT + sys.argv[1]).encode()).hexdigest())