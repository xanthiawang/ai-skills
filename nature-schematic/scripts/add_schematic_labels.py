#!/usr/bin/env python3
"""Create an editable SVG label overlay for a schematic base image."""

from __future__ import annotations

import argparse
import base64
import html
import struct
import sys
from pathlib import Path


def image_info(path: Path) -> tuple[int, int, str]:
    data = path.read_bytes()

    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        if len(data) < 24:
            raise SystemExit(f"Invalid PNG file: {path}")
        width, height = struct.unpack(">II", data[16:24])
        return width, height, "image/png"

    if data.startswith((b"GIF87a", b"GIF89a")):
        if len(data) < 10:
            raise SystemExit(f"Invalid GIF file: {path}")
        width, height = struct.unpack("<HH", data[6:10])
        return width, height, "image/gif"

    if data.startswith(b"\xff\xd8"):
        index = 2
        sof_markers = set(range(0xC0, 0xC4)) | set(range(0xC5, 0xC8)) | set(range(0xC9, 0xCC)) | set(range(0xCD, 0xD0))
        while index < len(data):
            if data[index] != 0xFF:
                index += 1
                continue
            while index < len(data) and data[index] == 0xFF:
                index += 1
            if index >= len(data):
                break
            marker = data[index]
            index += 1
            if marker in (0xD8, 0xD9):
                continue
            if index + 2 > len(data):
                break
            segment_length = struct.unpack(">H", data[index : index + 2])[0]
            if segment_length < 2 or index + segment_length > len(data):
                break
            if marker in sof_markers:
                if segment_length < 7:
                    break
                height, width = struct.unpack(">HH", data[index + 3 : index + 7])
                return width, height, "image/jpeg"
            index += segment_length
        raise SystemExit(f"Could not read JPEG dimensions: {path}")

    raise SystemExit(f"Unsupported base image type for SVG embedding: {path}")


def parse_label(value: str) -> tuple[str, float]:
    if ":" not in value:
        raise argparse.ArgumentTypeError("label must use TEXT:X_FRACTION, for example Human:0.11")
    text, x_value = value.rsplit(":", 1)
    text = text.strip()
    if not text:
        raise argparse.ArgumentTypeError("label text cannot be empty")
    try:
        x_fraction = float(x_value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"invalid x fraction: {x_value}") from exc
    if not 0.0 <= x_fraction <= 1.0:
        raise argparse.ArgumentTypeError("x fraction must be between 0 and 1")
    return text, x_fraction


def data_uri(path: Path) -> str:
    _, _, mime = image_info(path)
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def build_svg(
    base: Path,
    labels: list[tuple[str, float]],
    label_y: float,
    font_size: float,
    font_family: str,
) -> str:
    width, height, _ = image_info(base)
    y = label_y * height
    image_href = data_uri(base)

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        "  <title>Nature-style schematic with editable labels</title>",
        "  <defs>",
        "    <style>",
        (
            "      .label { "
            f"font-family: {html.escape(font_family)}; "
            f"font-size: {font_size:g}px; "
            "font-weight: 400; fill: #111111; letter-spacing: 0; "
            "}"
        ),
        "    </style>",
        "  </defs>",
        '  <rect width="100%" height="100%" fill="#ffffff"/>',
        f'  <image href="{image_href}" x="0" y="0" width="{width}" height="{height}" preserveAspectRatio="xMidYMid meet"/>',
    ]
    for text, x_fraction in labels:
        x = x_fraction * width
        lines.append(
            f'  <text class="label" x="{x:.2f}" y="{y:.2f}" '
            f'text-anchor="middle">{html.escape(text)}</text>'
        )
    lines.append("</svg>")
    return "\n".join(lines) + "\n"


def render_png(svg_path: Path, png_path: Path) -> None:
    try:
        import cairosvg
    except ImportError as exc:
        print(
            f"Warning: wrote SVG but cannot render PNG because cairosvg is not installed: {svg_path}",
            file=sys.stderr,
        )
        return
    cairosvg.svg2png(url=str(svg_path), write_to=str(png_path))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True, type=Path, help="Generated schematic base image")
    parser.add_argument("--out-svg", required=True, type=Path, help="Output editable SVG path")
    parser.add_argument("--out-png", type=Path, help="Optional PNG preview path")
    parser.add_argument("--label", action="append", type=parse_label, required=True, help="Label as TEXT:X_FRACTION")
    parser.add_argument("--label-y", type=float, default=0.87, help="Label baseline as image-height fraction")
    parser.add_argument("--font-size", type=float, default=32.0, help="Label font size in SVG pixels")
    parser.add_argument(
        "--font-family",
        default="Arial, Helvetica, sans-serif",
        help="SVG font-family value",
    )
    args = parser.parse_args()

    if not args.base.exists():
        raise SystemExit(f"Cannot proceed - required base image file not found: {args.base}")
    if not 0.0 <= args.label_y <= 1.0:
        raise SystemExit("--label-y must be between 0 and 1")

    args.out_svg.parent.mkdir(parents=True, exist_ok=True)
    svg = build_svg(args.base, args.label, args.label_y, args.font_size, args.font_family)
    args.out_svg.write_text(svg, encoding="utf-8")
    print(f"Wrote SVG: {args.out_svg}")

    if args.out_png:
        args.out_png.parent.mkdir(parents=True, exist_ok=True)
        render_png(args.out_svg, args.out_png)
        if args.out_png.exists():
            print(f"Wrote PNG: {args.out_png}")


if __name__ == "__main__":
    main()
