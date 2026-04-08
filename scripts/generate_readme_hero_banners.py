#!/usr/bin/env python3
"""Generate deterministic wide hero banner concepts for the README."""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter

WIDTH = 2400
HEIGHT = 1000
OUT_DIR = Path(__file__).resolve().parents[1] / "docs" / "readme_assets"


def rgb(hex_code: str) -> tuple[int, int, int]:
    hex_code = hex_code.lstrip("#")
    return tuple(int(hex_code[index : index + 2], 16) for index in (0, 2, 4))


def first_primes(count: int) -> np.ndarray:
    if count < 1:
        return np.array([], dtype=np.int64)
    if count < 6:
        limit = 15
    else:
        n = float(count)
        limit = int(n * (math.log(n) + math.log(math.log(n)))) + 20
    while True:
        sieve = np.ones(limit + 1, dtype=bool)
        sieve[:2] = False
        bound = int(limit**0.5) + 1
        for value in range(2, bound):
            if sieve[value]:
                sieve[value * value : limit + 1 : value] = False
        primes = np.flatnonzero(sieve)
        if primes.size >= count:
            return primes[:count]
        limit *= 2


def lpp_backbone(n: np.ndarray) -> np.ndarray:
    log_n = np.log(n)
    log_log_n = np.log(log_n)
    return n * (log_n + log_log_n - 1.0 + (log_log_n - 2.0) / log_n)


def make_canvas(color: str) -> Image.Image:
    return Image.new("RGBA", (WIDTH, HEIGHT), rgb(color) + (255,))


def mesh() -> tuple[np.ndarray, np.ndarray]:
    x = np.linspace(0.0, 1.0, WIDTH, dtype=np.float32)
    y = np.linspace(0.0, 1.0, HEIGHT, dtype=np.float32)
    return np.meshgrid(x, y)


def normalized_prime_features(count: int = 360) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    primes = first_primes(count)
    gaps = np.diff(primes, prepend=2)
    ratios = gaps / np.log(np.maximum(primes, 3))
    ratios = ratios / np.mean(ratios)
    return primes.astype(np.float64), gaps.astype(np.float64), ratios.astype(np.float64)


def y_from_backbone(sample_count: int) -> np.ndarray:
    n = np.geomspace(5.0, 2.0e8, sample_count)
    values = np.log(lpp_backbone(n))
    scaled = (values - values.min()) / (values.max() - values.min())
    return HEIGHT * (0.88 - 0.63 * scaled)


def polyline_layer(points: list[tuple[float, float]], color: tuple[int, int, int], width: int) -> Image.Image:
    layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    draw.line(points, fill=color + (255,), width=width, joint="curve")
    return layer


def glow_line(
    base: Image.Image,
    points: list[tuple[float, float]],
    color: tuple[int, int, int],
    width: int,
    glow_radius: int,
    glow_alpha: int = 150,
) -> None:
    layer = polyline_layer(points, color, width)
    glow = layer.copy()
    alpha = glow.getchannel("A").point(lambda value: min(glow_alpha, value))
    glow.putalpha(alpha)
    glow = glow.filter(ImageFilter.GaussianBlur(glow_radius))
    base.alpha_composite(glow)
    base.alpha_composite(layer)


def add_radial_glow(
    base: Image.Image,
    center_x: float,
    center_y: float,
    radius: float,
    color: tuple[int, int, int],
    strength: float,
) -> None:
    grid_x, grid_y = mesh()
    dx = grid_x - center_x
    dy = grid_y - center_y
    falloff = np.exp(-((dx * dx + dy * dy) / (radius * radius)))
    array = np.zeros((HEIGHT, WIDTH, 4), dtype=np.uint8)
    for channel, channel_value in enumerate(color):
        array[:, :, channel] = np.clip(channel_value * strength * falloff, 0, 255).astype(np.uint8)
    array[:, :, 3] = np.clip(220 * strength * falloff, 0, 255).astype(np.uint8)
    base.alpha_composite(Image.fromarray(array))


def add_grain(base: Image.Image, scale: float = 1.0) -> None:
    grid_x, grid_y = mesh()
    field = (
        np.sin(69.0 * grid_x + 41.0 * grid_y)
        + np.sin(127.0 * grid_x - 83.0 * grid_y)
        + np.cos(193.0 * grid_x + 151.0 * grid_y)
    )
    field = (field - field.min()) / (field.max() - field.min())
    alpha = np.clip(16.0 * scale * field, 0, 30).astype(np.uint8)
    layer = np.zeros((HEIGHT, WIDTH, 4), dtype=np.uint8)
    layer[:, :, :3] = 255
    layer[:, :, 3] = alpha
    base.alpha_composite(Image.fromarray(layer))


def banner_cosmic_backbone() -> Image.Image:
    base = make_canvas("#060914")
    add_radial_glow(base, 0.18, 0.42, 0.35, rgb("#00d7ff"), 1.15)
    add_radial_glow(base, 0.82, 0.58, 0.42, rgb("#ff6a00"), 0.9)
    add_radial_glow(base, 0.55, 0.18, 0.28, rgb("#7b2cff"), 0.8)

    grid = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(grid)
    x_values = np.linspace(0.0, WIDTH, 220)
    y_values = np.linspace(0.0, HEIGHT, 180)
    for x_line in np.linspace(140, WIDTH - 140, 17):
        points = []
        for y_line in y_values:
            x_offset = 45.0 * math.sin((y_line / HEIGHT) * 3.6 * math.pi + x_line * 0.0023)
            x_offset += 18.0 * math.sin((y_line / HEIGHT) * 10.5 * math.pi)
            points.append((x_line + x_offset, y_line))
        draw.line(points, fill=rgb("#73ecff") + (32,), width=2)
    for y_line in np.linspace(120, HEIGHT - 120, 10):
        points = []
        for x_line in x_values:
            y_offset = 38.0 * math.sin((x_line / WIDTH) * 3.0 * math.pi + y_line * 0.006)
            y_offset += 22.0 * math.sin((x_line / WIDTH) * 8.0 * math.pi)
            points.append((x_line, y_line + y_offset))
        draw.line(points, fill=rgb("#ffd86b") + (26,), width=2)
    base.alpha_composite(grid.filter(ImageFilter.GaussianBlur(0.5)))

    rings = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    ring_draw = ImageDraw.Draw(rings)
    ring_draw.ellipse((-260, 60, 1080, 1400), outline=rgb("#60f0ff") + (42,), width=6)
    ring_draw.ellipse((1120, -220, 2560, 1220), outline=rgb("#ff9b3d") + (48,), width=8)
    ring_draw.ellipse((760, 120, 1980, 1340), outline=rgb("#b35bff") + (28,), width=4)
    base.alpha_composite(rings.filter(ImageFilter.GaussianBlur(2.0)))

    sample_count = 560
    y_curve = y_from_backbone(sample_count)
    points = [
        (120 + index * (WIDTH - 240) / (sample_count - 1), float(y_curve[index] + 20.0 * math.sin(index / 44.0)))
        for index in range(sample_count)
    ]
    glow_line(base, points, rgb("#f6c24a"), width=9, glow_radius=26, glow_alpha=135)
    glow_line(base, [(x, y + 42.0) for x, y in points], rgb("#0ed8ff"), width=4, glow_radius=18, glow_alpha=110)

    primes, _, ratios = normalized_prime_features(280)
    x_positions = 140 + (np.log(primes) - np.log(primes.min())) / (np.log(primes.max()) - np.log(primes.min())) * (WIDTH - 280)
    y_prime_backbone = np.interp(x_positions, [point[0] for point in points], [point[1] for point in points])
    offsets = 58.0 * np.sin(primes * 0.11) * (ratios - 1.0)
    star_layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    star_draw = ImageDraw.Draw(star_layer)
    for index, x_pos in enumerate(x_positions):
        y_pos = float(y_prime_backbone[index] - offsets[index])
        radius = 2.5 + 2.6 * min(1.5, ratios[index])
        color = rgb("#fff4d4") if index % 5 else rgb("#7cf4ff")
        star_draw.ellipse(
            (x_pos - radius, y_pos - radius, x_pos + radius, y_pos + radius),
            fill=color + (245,),
        )
    star_layer = star_layer.filter(ImageFilter.GaussianBlur(1.5))
    base.alpha_composite(star_layer)

    halo = star_layer.filter(ImageFilter.GaussianBlur(8.0))
    halo.putalpha(halo.getchannel("A").point(lambda value: value // 2))
    base.alpha_composite(halo)

    add_grain(base, 0.7)
    return base


def palette_blend(values: np.ndarray, colors: list[tuple[int, int, int]]) -> np.ndarray:
    values = np.clip(values, 0.0, 1.0)
    segment = values * (len(colors) - 1)
    index = np.floor(segment).astype(np.int32)
    index = np.clip(index, 0, len(colors) - 2)
    blend = segment - index
    output = np.zeros(values.shape + (3,), dtype=np.float32)
    for channel in range(3):
        c0 = np.take([color[channel] for color in colors], index)
        c1 = np.take([color[channel] for color in colors], index + 1)
        output[:, :, channel] = c0 * (1.0 - blend) + c1 * blend
    return output


def banner_liquid_spectrum() -> Image.Image:
    grid_x, grid_y = mesh()
    spine = 0.52 + 0.17 * np.sin(2.4 * math.pi * np.power(grid_x, 0.85) + 0.25) - 0.09 * np.exp(-4.0 * grid_x)
    distance = np.abs(grid_y - spine)
    waves = (
        np.sin(9.0 * grid_x + 3.2 * np.sin(4.5 * grid_y))
        + np.cos(11.0 * grid_y - 2.7 * grid_x)
        + np.sin(15.0 * np.sqrt((grid_x - 0.18) ** 2 + (grid_y - 0.56) ** 2) - 3.8 * grid_x)
    )
    waves = (waves - waves.min()) / (waves.max() - waves.min())
    ribbon = np.exp(-np.power(distance / 0.085, 2.0))
    channels = np.exp(-np.power(distance / 0.18, 2.0))
    value_map = np.clip(0.08 + 0.72 * channels + 0.20 * waves, 0.0, 1.0)
    palette_index = np.mod(waves * 0.78 + 0.55 * ribbon + 0.12 * np.sin(18.0 * distance), 1.0)

    colors = [
        rgb("#09061a"),
        rgb("#1739b6"),
        rgb("#00c6ff"),
        rgb("#b6ff00"),
        rgb("#ff5fd2"),
        rgb("#ff8a00"),
        rgb("#09061a"),
    ]
    image_array = palette_blend(palette_index, colors)
    image_array *= value_map[:, :, None]

    shadow = np.exp(-np.power(distance / 0.045, 2.0))
    image_array *= (1.0 - 0.62 * shadow[:, :, None])

    base = Image.fromarray(np.clip(image_array, 0, 255).astype(np.uint8)).convert("RGBA")
    add_radial_glow(base, 0.16, 0.52, 0.20, rgb("#00f6ff"), 0.75)
    add_radial_glow(base, 0.80, 0.48, 0.25, rgb("#ff4bb1"), 0.78)

    primes, _, ratios = normalized_prime_features(240)
    x_positions = 120 + (np.log(primes) - np.log(primes.min())) / (np.log(primes.max()) - np.log(primes.min())) * (WIDTH - 240)
    x_norm = x_positions / WIDTH
    spine_y = 0.52 + 0.17 * np.sin(2.4 * math.pi * np.power(x_norm, 0.85) + 0.25) - 0.09 * np.exp(-4.0 * x_norm)
    y_positions = HEIGHT * spine_y + 28.0 * np.sin(primes * 0.07) * (ratios - 1.0)
    bead_layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    bead_draw = ImageDraw.Draw(bead_layer)
    for index, x_pos in enumerate(x_positions):
        y_pos = float(y_positions[index])
        radius = 4.0 if index % 7 == 0 else 2.6
        color = rgb("#fff5a6") if index % 7 == 0 else rgb("#ffffff")
        bead_draw.ellipse((x_pos - radius, y_pos - radius, x_pos + radius, y_pos + radius), fill=color + (245,))
    bead_glow = bead_layer.filter(ImageFilter.GaussianBlur(7.0))
    bead_glow.putalpha(bead_glow.getchannel("A").point(lambda value: value // 2))
    base.alpha_composite(bead_glow)
    base.alpha_composite(bead_layer)

    veil = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    veil_draw = ImageDraw.Draw(veil)
    for offset in (-120, -60, 60, 120):
        points = []
        for x_pos in np.linspace(0, WIDTH, 420):
            x_norm = x_pos / WIDTH
            center = HEIGHT * (
                0.52
                + 0.17 * math.sin(2.4 * math.pi * math.pow(max(x_norm, 1e-6), 0.85) + 0.25)
                - 0.09 * math.exp(-4.0 * x_norm)
            )
            points.append((x_pos, center + offset + 14.0 * math.sin(x_norm * 8.0 * math.pi + offset * 0.03)))
        veil_draw.line(points, fill=rgb("#ffffff") + (14,), width=3)
    base.alpha_composite(veil.filter(ImageFilter.GaussianBlur(2.0)))
    add_grain(base, 0.45)
    return base


def make_paper_background() -> Image.Image:
    grid_x, grid_y = mesh()
    vertical = 0.94 - 0.08 * grid_y
    fiber = 0.04 * np.sin(34.0 * grid_x + 9.0 * grid_y) + 0.03 * np.sin(97.0 * grid_x - 53.0 * grid_y)
    tone = np.clip(vertical + fiber, 0.0, 1.0)
    color_a = np.array(rgb("#f7edd6"), dtype=np.float32)
    color_b = np.array(rgb("#e6d8bf"), dtype=np.float32)
    array = color_b + (color_a - color_b) * tone[:, :, None]
    return Image.fromarray(np.clip(array, 0, 255).astype(np.uint8)).convert("RGBA")


def banner_screenprint_orbits() -> Image.Image:
    base = make_paper_background()
    paper = base.copy()

    dark_disc = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    disc_draw = ImageDraw.Draw(dark_disc)
    disc_draw.ellipse((1320, -260, 2620, 1040), fill=rgb("#151521") + (255,))
    disc_draw.ellipse((1485, -95, 2450, 870), outline=rgb("#f0c14d") + (110,), width=6)
    disc_draw.ellipse((1600, 10, 2330, 740), outline=rgb("#4f8df5") + (120,), width=9)
    disc_draw.ellipse((1720, 120, 2210, 610), outline=rgb("#f05a28") + (85,), width=12)
    base.alpha_composite(dark_disc)

    primes, _, ratios = normalized_prime_features(190)
    x_positions = 160 + (np.log(primes) - np.log(primes.min())) / (np.log(primes.max()) - np.log(primes.min())) * (WIDTH - 320)

    ribbon_x = np.linspace(160.0, WIDTH - 160.0, 68)
    ribbon_norm = ribbon_x / WIDTH
    ribbon_y = HEIGHT * (
        0.60
        - 0.12 * np.sin(np.power(ribbon_norm, 0.84) * math.pi * 1.08 + 0.32)
        - 0.05 * ribbon_norm
    )

    ratio_on_ribbon = np.interp(ribbon_x, x_positions, ratios)
    cobalt_points = [(float(ribbon_x[i]), float(ribbon_y[i])) for i in range(ribbon_x.size)]
    rust_points = [(x, y + 78.0) for x, y in cobalt_points]
    gold_points = [
        (x, y - 30.0 - 10.0 * (ratio_on_ribbon[index] - 1.0))
        for index, (x, y) in enumerate(cobalt_points)
    ]

    glow_line(base, rust_points, rgb("#d95b2b"), width=54, glow_radius=3, glow_alpha=220)
    glow_line(base, cobalt_points, rgb("#275cc6"), width=72, glow_radius=3, glow_alpha=230)
    glow_line(base, gold_points, rgb("#f2c14e"), width=18, glow_radius=8, glow_alpha=140)

    bars = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    bar_draw = ImageDraw.Draw(bars)
    bar_draw.polygon([(0, 760), (540, 600), (540, 1000), (0, 1000)], fill=rgb("#f05a28") + (180,))
    bar_draw.polygon([(0, 0), (420, 0), (920, 380), (580, 470)], fill=rgb("#2b4a8b") + (110,))
    bar_draw.polygon([(1070, 0), (1360, 0), (1680, 240), (1450, 300)], fill=rgb("#f0c14d") + (90,))
    base.alpha_composite(bars)

    bead_layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    bead_draw = ImageDraw.Draw(bead_layer)
    y_beads = np.interp(x_positions, ribbon_x, [point[1] for point in gold_points])
    bead_offsets = -10.0 * np.sin(primes * 0.09) * (ratios - 1.0)
    for index, x_pos in enumerate(x_positions):
        y_pos = float(y_beads[index] + bead_offsets[index])
        radius = 6.0 if index % 9 == 0 else 3.8
        fill = rgb("#f7edd6") if index % 9 == 0 else rgb("#151521")
        bead_draw.ellipse((x_pos - radius, y_pos - radius, x_pos + radius, y_pos + radius), fill=fill + (230,))
    base.alpha_composite(bead_layer)

    contour = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    contour_draw = ImageDraw.Draw(contour)
    for offset in (-140, -70, 70, 140):
        shifted = [(x, y + offset) for x, y in cobalt_points]
        contour_draw.line(shifted, fill=rgb("#151521") + (38,), width=3)
    base.alpha_composite(contour.filter(ImageFilter.GaussianBlur(1.0)))
    add_grain(base, 0.35)
    base = Image.blend(paper, base, 0.98)
    return base


def save_image(image: Image.Image, path: Path) -> None:
    image.convert("RGB").save(path, format="PNG", optimize=True)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    outputs = {
        "hero_banner_concept_1_cosmic_backbone.png": banner_cosmic_backbone(),
        "hero_banner_concept_2_liquid_spectrum.png": banner_liquid_spectrum(),
        "hero_banner_concept_3_screenprint_orbits.png": banner_screenprint_orbits(),
    }
    for name, image in outputs.items():
        save_image(image, OUT_DIR / name)
        print(OUT_DIR / name)
    save_image(outputs["hero_banner_concept_1_cosmic_backbone.png"], OUT_DIR / "readme_hero_cosmic_backbone.png")
    print(OUT_DIR / "readme_hero_cosmic_backbone.png")


if __name__ == "__main__":
    main()
