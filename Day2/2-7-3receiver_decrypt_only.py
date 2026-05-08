#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass


# ============================================================
# CONFIG: 主にここを編集
# ============================================================
CONFIG = {
    "receiver_id": "87654321",
    "receiver_private_key_file": "receiver_private_key_87654321.json",
    "secure_message_file": "secure_message_12345678_to_87654321.json",
}
# ============================================================


Point = tuple[int, int] | None


@dataclass(frozen=True)
class EllipticCurve:
    p: int
    a: int
    b: int

    def is_on_curve(self, point: Point) -> bool:
        if point is None:
            return True
        x, y = point
        return (y * y - (x * x * x + self.a * x + self.b)) % self.p == 0


def validate_id(value: str, name: str) -> None:
    if len(value) != 8 or not value.isdigit():
        raise ValueError(f"{name} must be exactly 8 digits")


def mod_inverse(a: int, m: int) -> int:
    a %= m
    if a == 0:
        raise ZeroDivisionError("inverse does not exist")
    return pow(a, -1, m)


def point_add(curve: EllipticCurve, p1: Point, p2: Point) -> Point:
    if p1 is None:
        return p2
    if p2 is None:
        return p1

    x1, y1 = p1
    x2, y2 = p2
    p = curve.p

    if x1 == x2 and (y1 + y2) % p == 0:
        return None

    if p1 != p2:
        numerator = (y2 - y1) % p
        denominator = (x2 - x1) % p
    else:
        if y1 % p == 0:
            return None
        numerator = (3 * x1 * x1 + curve.a) % p
        denominator = (2 * y1) % p

    slope = (numerator * mod_inverse(denominator, p)) % p
    x3 = (slope * slope - x1 - x2) % p
    y3 = (slope * (x1 - x3) - y1) % p

    result = (x3, y3)
    if not curve.is_on_curve(result):
        raise ValueError("resulting point is not on the curve")
    return result


def scalar_mult(curve: EllipticCurve, k: int, point: Point) -> Point:
    if k < 0:
        raise ValueError("k must be non-negative")
    if point is not None and not curve.is_on_curve(point):
        raise ValueError("point is not on the curve")

    result: Point = None
    addend = point

    while k > 0:
        if k & 1:
            result = point_add(curve, result, addend)
        addend = point_add(curve, addend, addend)
        k >>= 1

    return result


def dict_to_point(data: dict[str, int]) -> Point:
    return (data["x"], data["y"])


def derive_stream_key(shared_point: Point, out_len: int) -> bytes:
    if shared_point is None:
        raise ValueError("shared_point must not be None")

    seed = f"{shared_point[0]}:{shared_point[1]}".encode("utf-8")
    out = bytearray()
    counter = 0

    while len(out) < out_len:
        block = hashlib.sha256(seed + counter.to_bytes(4, "big")).digest()
        out.extend(block)
        counter += 1

    return bytes(out[:out_len])


def xor_bytes(data: bytes, key: bytes) -> bytes:
    return bytes(d ^ k for d, k in zip(data, key))


def main() -> int:
    receiver_id = CONFIG["receiver_id"]
    validate_id(receiver_id, "receiver_id")

    with open(CONFIG["receiver_private_key_file"], "r", encoding="utf-8") as f:
        receiver_priv = json.load(f)

    with open(CONFIG["secure_message_file"], "r", encoding="utf-8") as f:
        secure = json.load(f)

    if receiver_priv["receiver_id"] != receiver_id:
        raise ValueError("receiver_id mismatch in private key file")

    if secure["receiver_id"] != receiver_id:
        raise ValueError("receiver_id mismatch in secure message file")

    curve = EllipticCurve(
        p=receiver_priv["curve"]["p"],
        a=receiver_priv["curve"]["a"],
        b=receiver_priv["curve"]["b"],
    )

    base_point = dict_to_point(receiver_priv["base_point"])
    receiver_private_key = receiver_priv["private_key"]
    receiver_public_key = dict_to_point(receiver_priv["public_key"])
    ephemeral_public_key = dict_to_point(secure["ephemeral_public_key"])
    ciphertext_hex = secure["ciphertext_hex"]

    if not curve.is_on_curve(base_point):
        raise ValueError("base point is not on curve")
    if not curve.is_on_curve(receiver_public_key):
        raise ValueError("receiver public key is not on curve")
    if not curve.is_on_curve(ephemeral_public_key):
        raise ValueError("ephemeral public key is not on curve")

    shared_point = scalar_mult(curve, receiver_private_key, ephemeral_public_key)
    if shared_point is None:
        raise ValueError("shared secret generation failed")

    ciphertext = bytes.fromhex(ciphertext_hex)
    stream_key = derive_stream_key(shared_point, len(ciphertext))
    plaintext_bytes = xor_bytes(ciphertext, stream_key)

    try:
        plaintext = plaintext_bytes.decode("utf-8")
    except UnicodeDecodeError:
        plaintext = plaintext_bytes.decode("utf-8", errors="replace")
        print("warning: UTF-8 として完全には復号できませんでした。改ざんや不整合の可能性があります。")

    print("=== receiver decrypt only ===")
    print(f"receiver id       = {receiver_id}")
    print(f"sender id         = {secure['sender_id']}")
    print(f"ephemeral public  = {ephemeral_public_key}")
    print(f"shared secret     = {shared_point}")
    print(f"ciphertext hex    = {ciphertext_hex}")
    print(f"plaintext         = {plaintext}")
    print()
    print("注意:")
    print("このスクリプトは署名検証を行わず、復号だけを実行します。")
    print("改ざん確認が必要な場合は receiver_secure.py を使ってください。")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())