"""Colour checks for prototype tokens: CIEDE2000 distance, WCAG contrast, OKLab ramp.

Usage:
  python3 color_tools.py '#0B7285' '#2F63B8' '#2F6B4A'      # pairwise ΔE2000 + contrast vs white/black
  python3 color_tools.py ramp '#5284D7' '#212021' 7          # 7-step OKLab ramp between two colours
"""
import math, sys


def _srgb(h):
    h = h.lstrip('#')
    return [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]


def _lin(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def luminance(h):
    r, g, b = [_lin(c) for c in _srgb(h)]
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    la, lb = luminance(a), luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def to_lab(h):
    r, g, b = [_lin(c) for c in _srgb(h)]
    x = (0.4124 * r + 0.3576 * g + 0.1805 * b) / 0.95047
    y = (0.2126 * r + 0.7152 * g + 0.0722 * b)
    z = (0.0193 * r + 0.1192 * g + 0.9505 * b) / 1.08883
    f = lambda t: t ** (1 / 3) if t > 0.008856 else 7.787 * t + 16 / 116
    return 116 * f(y) - 16, 500 * (f(x) - f(y)), 200 * (f(y) - f(z))


def de2000(c1, c2):
    L1, a1, b1 = to_lab(c1); L2, a2, b2 = to_lab(c2)
    avg_L = (L1 + L2) / 2
    C1 = math.hypot(a1, b1); C2 = math.hypot(a2, b2); avg_C = (C1 + C2) / 2
    G = 0.5 * (1 - math.sqrt(avg_C ** 7 / (avg_C ** 7 + 25 ** 7)))
    a1p, a2p = (1 + G) * a1, (1 + G) * a2
    C1p, C2p = math.hypot(a1p, b1), math.hypot(a2p, b2); avg_Cp = (C1p + C2p) / 2
    h1p = math.degrees(math.atan2(b1, a1p)) % 360; h2p = math.degrees(math.atan2(b2, a2p)) % 360
    dhp = h2p - h1p
    if abs(dhp) > 180: dhp -= 360 * (1 if dhp > 0 else -1)
    dHp = 2 * math.sqrt(C1p * C2p) * math.sin(math.radians(dhp / 2))
    avg_hp = (h1p + h2p + (360 if abs(h1p - h2p) > 180 else 0)) / 2
    T = 1 - 0.17 * math.cos(math.radians(avg_hp - 30)) + 0.24 * math.cos(math.radians(2 * avg_hp)) \
        + 0.32 * math.cos(math.radians(3 * avg_hp + 6)) - 0.20 * math.cos(math.radians(4 * avg_hp - 63))
    dLp, dCp = L2 - L1, C2p - C1p
    SL = 1 + 0.015 * (avg_L - 50) ** 2 / math.sqrt(20 + (avg_L - 50) ** 2)
    SC = 1 + 0.045 * avg_Cp; SH = 1 + 0.015 * avg_Cp * T
    RT = -2 * math.sqrt(avg_Cp ** 7 / (avg_Cp ** 7 + 25 ** 7)) * math.sin(math.radians(60 * math.exp(-((avg_hp - 275) / 25) ** 2)))
    return math.sqrt((dLp / SL) ** 2 + (dCp / SC) ** 2 + (dHp / SH) ** 2 + RT * (dCp / SC) * (dHp / SH))


def to_oklab(h):
    r, g, b = [_lin(c) for c in _srgb(h)]
    l = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b
    m = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b
    s = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b
    l, m, s = l ** (1 / 3), m ** (1 / 3), s ** (1 / 3)
    return (0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s,
            1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s,
            0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s)


def from_oklab(L, a, b):
    l = (L + 0.3963377774 * a + 0.2158037573 * b) ** 3
    m = (L - 0.1055613458 * a - 0.0638541728 * b) ** 3
    s = (L - 0.0894841775 * a - 1.2914855480 * b) ** 3
    r = 4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s
    g = -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s
    bb = -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s
    enc = lambda c: 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055
    return '#%02x%02x%02x' % tuple(max(0, min(255, round(enc(c) * 255))) for c in (r, g, bb))


def ramp(c1, c2, n):
    A, B = to_oklab(c1), to_oklab(c2)
    return [from_oklab(*[A[i] + (B[i] - A[i]) * k / (n - 1) for i in range(3)]) for k in range(n)]


if __name__ == '__main__':
    args = sys.argv[1:]
    if not args:
        print(__doc__); sys.exit(0)
    if args[0] == 'ramp':
        print(' '.join(ramp(args[1], args[2], int(args[3]) if len(args) > 3 else 7))); sys.exit(0)
    for c in args:
        print(f"{c}  on white {contrast(c, '#FFFFFF'):5.2f}  on black {contrast(c, '#000000'):5.2f}  "
              + ('AA' if contrast(c, '#FFFFFF') >= 4.5 else 'fail-on-white'))
    for i in range(len(args)):
        for j in range(i + 1, len(args)):
            print(f"ΔE2000 {args[i]} ↔ {args[j]}: {de2000(args[i], args[j]):.1f}")
