#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import random
from dataclasses import dataclass


# ============================================================
# CONFIG: 主にここを編集
# ============================================================
CONFIG = {
    "random_seed": 99,

    "sender_id": "12345678",
    "receiver_id": "87654321",

    # 学習用の小さい曲線
    # 実運用では secp256k1 などの標準曲線を使う
    "curve_p": 17,
    "curve_a": 2,
    "curve_b": 2,
    "min_order": 19,

    # 実行モード
    # True なら受信者鍵生成
    # False なら署名検証 + 復号
    # "generate_receiver_keypair": True,
    "generate_receiver_keypair": False,

    # ファイル名
    "receiver_public_key_file": "receiver_public_key_87654321.json",
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


def point_order(curve: EllipticCurve, point: Point, max_iter: int = 10000) -> int:
    if point is None:
        return 1

    acc: Point = None
    for n in range(1, max_iter + 1):
        acc = point_add(curve, acc, point)
        if acc is None:
            return n

    raise ValueError("order search exceeded max_iter")


def list_points(curve: EllipticCurve) -> list[Point]:
    points: list[Point] = [None]
    for x in range(curve.p):
        rhs = (x * x * x + curve.a * x + curve.b) % curve.p
        for y in range(curve.p):
            if (y * y) % curve.p == rhs:
                points.append((x, y))
    return points


def is_prime(n: int) -> bool:
    if n < 2:
        return False
    if n in (2, 3):
        return True
    if n % 2 == 0:
        return False
    d = 3
    while d * d <= n:
        if n % d == 0:
            return False
        d += 2
    return True


def find_base_point_with_prime_order(curve: EllipticCurve, min_order: int) -> tuple[Point, int]:
    for pt in list_points(curve):
        if pt is None:
            continue
        n = point_order(curve, pt)
        if n >= min_order and is_prime(n):
            return pt, n
    raise ValueError("no suitable base point with prime order found")


def point_to_dict(point: Point) -> dict[str, int]:
    if point is None:
        raise ValueError("point must not be None")
    return {"x": point[0], "y": point[1]}


def dict_to_point(data: dict[str, int]) -> Point:
    return (data["x"], data["y"])


def hash_bytes(data: bytes) -> int:
    digest = hashlib.sha256(data).digest()
    return int.from_bytes(digest, "big")


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


def canonical_signature_message(
    sender_id: str,
    receiver_id: str,
    ephemeral_public: Point,
    ciphertext_hex: str,
) -> bytes:
    if ephemeral_public is None:
        raise ValueError("ephemeral_public must not be None")
    text = (
        f"sender_id={sender_id}|"
        f"receiver_id={receiver_id}|"
        f"ephemeral_x={ephemeral_public[0]}|"
        f"ephemeral_y={ephemeral_public[1]}|"
        f"ciphertext_hex={ciphertext_hex}"
    )
    return text.encode("utf-8")


def ecdsa_verify(
    curve: EllipticCurve,
    base_point: Point,
    order: int,
    public_key: Point,
    message_bytes: bytes,
    signature: tuple[int, int],
) -> bool:
    if public_key is None or not curve.is_on_curve(public_key):
        return False

    r, s = signature
    if not (1 <= r < order and 1 <= s < order):
        return False

    z = hash_bytes(message_bytes) % order
    w = mod_inverse(s, order)

    u1 = (z * w) % order
    u2 = (r * w) % order

    p1 = scalar_mult(curve, u1, base_point)
    p2 = scalar_mult(curve, u2, public_key)
    x = point_add(curve, p1, p2)

    if x is None:
        return False

    x1, _ = x
    return (x1 % order) == r


def generate_receiver_keypair() -> None:
    seed = CONFIG["random_seed"]
    if seed is not None:
        random.seed(seed)

    receiver_id = CONFIG["receiver_id"]
    validate_id(receiver_id, "receiver_id")

    curve = EllipticCurve(
        p=CONFIG["curve_p"],
        a=CONFIG["curve_a"],
        b=CONFIG["curve_b"],
    )

    discriminant = (4 * curve.a**3 + 27 * curve.b**2) % curve.p
    if discriminant == 0:
        raise ValueError("invalid curve: discriminant is 0")

    base_point, order = find_base_point_with_prime_order(curve, CONFIG["min_order"])
    private_key = random.randint(1, order - 1)
    public_key = scalar_mult(curve, private_key, base_point)

    if public_key is None:
        raise ValueError("receiver public key generation failed")

    public_payload = {
        "receiver_id": receiver_id,
        "curve": {"p": curve.p, "a": curve.a, "b": curve.b},
        "base_point": point_to_dict(base_point),
        "order": order,
        "public_key": point_to_dict(public_key),
    }

    private_payload = {
        "receiver_id": receiver_id,
        "curve": {"p": curve.p, "a": curve.a, "b": curve.b},
        "base_point": point_to_dict(base_point),
        "order": order,
        "private_key": private_key,
        "public_key": point_to_dict(public_key),
    }

    with open(CONFIG["receiver_public_key_file"], "w", encoding="utf-8") as f:
        json.dump(public_payload, f, ensure_ascii=False, indent=2)

    with open(CONFIG["receiver_private_key_file"], "w", encoding="utf-8") as f:
        json.dump(private_payload, f, ensure_ascii=False, indent=2)

    print("=== receiver key generation ===")
    print(f"receiver id      = {receiver_id}")
    print(f"private key d    = {private_key}")
    print(f"public key Q     = {public_key}")
    print(f"G                = {base_point}")
    print(f"n                = {order}")
    print(f"saved public     = {CONFIG['receiver_public_key_file']}")
    print(f"saved private    = {CONFIG['receiver_private_key_file']}")


def verify_and_decrypt() -> None:
    sender_id = CONFIG["sender_id"]
    receiver_id = CONFIG["receiver_id"]
    validate_id(sender_id, "sender_id")
    validate_id(receiver_id, "receiver_id")

    with open(CONFIG["receiver_private_key_file"], "r", encoding="utf-8") as f:
        receiver_priv = json.load(f)

    with open(CONFIG["secure_message_file"], "r", encoding="utf-8") as f:
        secure = json.load(f)

    if receiver_priv["receiver_id"] != receiver_id:
        raise ValueError("receiver_id mismatch in private key file")

    if secure["receiver_id"] != receiver_id:
        raise ValueError("receiver_id mismatch in secure message file")

    if secure["sender_id"] != sender_id:
        raise ValueError("sender_id mismatch in secure message file")

    curve = EllipticCurve(
        p=receiver_priv["curve"]["p"],
        a=receiver_priv["curve"]["a"],
        b=receiver_priv["curve"]["b"],
    )

    base_point = dict_to_point(receiver_priv["base_point"])
    order = receiver_priv["order"]
    receiver_private_key = receiver_priv["private_key"]

    sender_public_key = dict_to_point(secure["sender_public_key"])
    ephemeral_public_key = dict_to_point(secure["ephemeral_public_key"])
    ciphertext_hex = secure["ciphertext_hex"]
    signature = (secure["signature"]["r"], secure["signature"]["s"])

    if not curve.is_on_curve(base_point):
        raise ValueError("base point is not on curve")
    if not curve.is_on_curve(sender_public_key):
        raise ValueError("sender public key is not on curve")
    if not curve.is_on_curve(ephemeral_public_key):
        raise ValueError("ephemeral public key is not on curve")

    signature_bytes = canonical_signature_message(
        sender_id=sender_id,
        receiver_id=receiver_id,
        ephemeral_public=ephemeral_public_key,
        ciphertext_hex=ciphertext_hex,
    )

    verified = ecdsa_verify(
        curve=curve,
        base_point=base_point,
        order=order,
        public_key=sender_public_key,
        message_bytes=signature_bytes,
        signature=signature,
    )

    print("=== receiver verify ===")
    print(f"sender id         = {sender_id}")
    print(f"receiver id       = {receiver_id}")
    print(f"signature (r, s)  = {signature}")
    print(f"verified          = {verified}")

    if not verified:
        print("署名検証に失敗したため、復号を中止します。")
        return

    shared_point = scalar_mult(curve, receiver_private_key, ephemeral_public_key)
    if shared_point is None:
        raise ValueError("shared secret generation failed")

    ciphertext = bytes.fromhex(ciphertext_hex)
    stream_key = derive_stream_key(shared_point, len(ciphertext))
    plaintext = xor_bytes(ciphertext, stream_key).decode("utf-8")

    print("=== receiver decrypt ===")
    print(f"ephemeral public  = {ephemeral_public_key}")
    print(f"shared secret     = {shared_point}")
    print(f"plaintext         = {plaintext}")
    print()
    print("学習ポイント:")
    print("1. 署名で改ざん検出と送信者確認を行う")
    print("2. 暗号化で受信者だけが読めるようにする")
    print("3. 署名検証成功後にだけ復号する")
    print("4. 送信者: kQ, 受信者: dR で同じ共有秘密を得る")


def main() -> int:
    if CONFIG["generate_receiver_keypair"]:
        generate_receiver_keypair()
    else:
        verify_and_decrypt()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
