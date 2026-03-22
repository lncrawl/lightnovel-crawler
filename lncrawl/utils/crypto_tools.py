import os

import base58


def generate_token() -> str:
    return base58.b58encode(os.urandom(7)).decode("ascii")
