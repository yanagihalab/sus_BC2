#!/usr/bin/env python3
from __future__ import annotations

import math

import matplotlib.pyplot as plt


CONFIG = {
    "curve_a": 2,
    "curve_b": 2,
    "curve_p": 17,

    "x_min": -5.0,
    "x_max": 5.0,
    "x_step": 0.01,

    "annotate_finite_points": True,

    "show_real_curve": True,
    "show_finite_field_points": True,

    "output_file": "elliptic_curve_visualization.png",
    "output_dpi": 200,
}


def real_curve_rhs(x: float, a: float, b: float) -> float:
    return x**3 + a * x + b


def generate_real_curve_points(
    a: float,
    b: float,
    x_min: float,
    x_max: float,
    x_step: float,
) -> tuple[list[float], list[float], list[float]]:
    xs: list[float] = []
    ys_pos: list[float] = []
    ys_neg: list[float] = []

    x = x_min
    while x <= x_max:
        rhs = real_curve_rhs(x, a, b)
        if rhs >= 0:
            y = math.sqrt(rhs)
            xs.append(x)
            ys_pos.append(y)
            ys_neg.append(-y)
        x += x_step

    return xs, ys_pos, ys_neg


def generate_finite_field_points(p: int, a: int, b: int) -> list[tuple[int, int]]:
    points: list[tuple[int, int]] = []
    for x in range(p):
        rhs = (x**3 + a * x + b) % p
        for y in range(p):
            if (y * y) % p == rhs:
                points.append((x, y))
    return points


def discriminant_mod_p(p: int, a: int, b: int) -> int:
    return (4 * a**3 + 27 * b**2) % p


def main() -> int:
    a = CONFIG["curve_a"]
    b = CONFIG["curve_b"]
    p = CONFIG["curve_p"]

    disc = discriminant_mod_p(p, a, b)
    if disc == 0:
        raise ValueError(
            "invalid curve over finite field: discriminant is 0. "
            "CONFIG の curve_a, curve_b, curve_p を見直してください。"
        )

    if CONFIG["show_real_curve"] and CONFIG["show_finite_field_points"]:
        fig, axes = plt.subplots(1, 2, figsize=(14, 6))
        ax_real = axes[0]
        ax_finite = axes[1]
    elif CONFIG["show_real_curve"]:
        fig, ax_real = plt.subplots(figsize=(7, 6))
        ax_finite = None
    elif CONFIG["show_finite_field_points"]:
        fig, ax_finite = plt.subplots(figsize=(7, 6))
        ax_real = None
    else:
        raise ValueError("at least one of show_real_curve / show_finite_field_points must be True")

    if ax_real is not None:
        xs, ys_pos, ys_neg = generate_real_curve_points(
            a=a,
            b=b,
            x_min=CONFIG["x_min"],
            x_max=CONFIG["x_max"],
            x_step=CONFIG["x_step"],
        )

        ax_real.plot(xs, ys_pos, label=r"$y = +\sqrt{x^3 + ax + b}$")
        ax_real.plot(xs, ys_neg, label=r"$y = -\sqrt{x^3 + ax + b}$")
        ax_real.axhline(0, linewidth=1)
        ax_real.axvline(0, linewidth=1)
        ax_real.set_title(f"Real curve: y^2 = x^3 + {a}x + {b}")
        ax_real.set_xlabel("x")
        ax_real.set_ylabel("y")
        ax_real.grid(True)
        ax_real.legend()

    if ax_finite is not None:
        ff_points = generate_finite_field_points(p=p, a=a, b=b)

        xs_ff = [pt[0] for pt in ff_points]
        ys_ff = [pt[1] for pt in ff_points]

        ax_finite.scatter(xs_ff, ys_ff)
        ax_finite.set_title(f"Finite field points: y^2 = x^3 + {a}x + {b} (mod {p})")
        ax_finite.set_xlabel("x mod p")
        ax_finite.set_ylabel("y mod p")
        ax_finite.set_xlim(-0.5, p - 0.5)
        ax_finite.set_ylim(-0.5, p - 0.5)
        ax_finite.set_xticks(range(p))
        ax_finite.set_yticks(range(p))
        ax_finite.grid(True)

        if CONFIG["annotate_finite_points"]:
            for x, y in ff_points:
                ax_finite.annotate(
                    f"({x},{y})",
                    (x, y),
                    xytext=(4, 4),
                    textcoords="offset points",
                    fontsize=8
                )

    fig.suptitle(
        "Elliptic curve visualization\n"
        "Note: production systems use finite fields; real-number plots are for intuition."
    )

    plt.tight_layout()
    plt.savefig(CONFIG["output_file"], dpi=CONFIG["output_dpi"], bbox_inches="tight")
    print("saved:", CONFIG["output_file"])
    plt.close(fig)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
