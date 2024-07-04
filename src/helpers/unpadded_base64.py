from base64 import urlsafe_b64encode, urlsafe_b64decode


def unpadded_base64_encode(decoded: str) -> str:
    return urlsafe_b64encode(decoded.encode()).decode().rstrip("=")


def unpadded_base64_decode(encoded: str) -> str:
    return urlsafe_b64decode((encoded + "=" * (len(encoded) % 4)).encode()).decode()
