#!/usr/bin/env python3
"""
Animated ASCII automaton banner with an optional block wordmark.

Automaton families:
  1D elementary rules  - spacetime triangles; frames scroll the window
  2D life-like (B/S)   - real 2D evolution; frames are generations
  brain / cyclic       - multi-state 2D

Wordmark: block | narrow | heavy fonts, solid / knockout / outline.
"""

import argparse
import random

import automata as A
from fonts import FONTS, font_dims

RAMP = ".:-=+*#%@"


# ----------------------------------------------------------------- glyphing

def render_1d(window, ramp):
    rows, cols = len(window), len(window[0])
    out = []
    for y in range(rows):
        line = []
        for x in range(cols):
            if not window[y][x]:
                line.append(" ")
                continue
            d = 0
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    if dx == 0 and dy == 0:
                        continue
                    yy, xx = y + dy, (x + dx) % cols
                    if 0 <= yy < rows and window[yy][xx]:
                        d += 1
            line.append(ramp[min(d, len(ramp) - 1)])
        lines_append = out.append
        lines_append("".join(line))
    return out


def render_2d(g, ramp, kind, nstates=8):
    rows, cols = len(g), len(g[0])
    out = []
    for y in range(rows):
        line = []
        for x in range(cols):
            s = g[y][x]
            if kind == "cyclic":
                line.append(ramp[min(int(s * len(ramp) / nstates), len(ramp) - 1)])
            elif kind == "brain":
                line.append(" " if s == 0 else
                            (ramp[len(ramp) // 3] if s == 1 else ramp[-1]))
            else:
                if not s:
                    line.append(" ")
                    continue
                n = A.neigh_count(g, y, x, rows, cols)
                line.append(ramp[min(n, len(ramp) - 1)])
        out.append("".join(line))
    return out


# ----------------------------------------------------------------- wordmark

def build_mask(text, cols, rows, font_name="block", sx=None, sy=None,
               italic=0.0, bold=False, offset_y=0):
    font = FONTS[font_name]
    fw, fh = font_dims(font)
    chars = [c for c in text.upper() if c in font]
    if not chars:
        return set(), set()

    if sx is None:
        sx = max(1, min(6, cols // (len(chars) * (fw + 1))))
    if sy is None:
        sy = max(1, int(round(sx * 0.62)))

    gw = (fw + 1) * sx
    tw = gw * len(chars) - sx
    th = fh * sy
    shear = int(round(th * italic))
    x0 = (cols - tw - shear) // 2
    y0 = (rows - th) // 2 + offset_y

    mask = set()
    for ci, ch in enumerate(chars):
        rows_bits = font[ch]
        for fy in range(fh):
            for fx in range(fw):
                if rows_bits[fy][fx] != "#":
                    continue
                for dy in range(sy):
                    for dx in range(sx):
                        rit = fy * sy + dy
                        lean = int(round((th - 1 - rit) * italic))
                        yy = y0 + rit
                        xx = x0 + ci * gw + fx * sx + dx + lean
                        if 0 <= yy < rows and 0 <= xx < cols:
                            mask.add((yy, xx))
                            if bold and xx + 1 < cols:
                                mask.add((yy, xx + 1))

    outline = set()
    for (y, x) in mask:
        for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            if (y + dy, x + dx) not in mask:
                outline.add((y, x))
                break
    return mask, outline


def dilate(cells, rows, cols, r=1):
    out = set()
    for (y, x) in cells:
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                yy, xx = y + dy, x + dx
                if 0 <= yy < rows and 0 <= xx < cols:
                    out.add((yy, xx))
    return out


def apply_mask(lines, mask, outline, mode, ramp, halo=True):
    if mode == "off" or not mask:
        return lines
    rows, cols = len(lines), len(lines[0])
    grid = [list(l) for l in lines]
    dense = ramp[-1]

    if halo:
        fill = dense if mode == "knockout" else " "
        for (y, x) in dilate(mask, rows, cols, 1) - mask:
            grid[y][x] = fill

    for (y, x) in mask:
        if mode == "knockout":
            grid[y][x] = " "
        elif mode == "solid":
            grid[y][x] = dense
        elif mode == "outline":
            grid[y][x] = dense if (y, x) in outline else " "

    return ["".join(r) for r in grid]


# ---------------------------------------------------------------------- svg

def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


GRADIENTS = {
    "h":        lambda w, h: (0, 0, w, 0),
    "v":        lambda w, h: (0, 0, 0, h),
    "diag":     lambda w, h: (0, 0, w, h),
    "diag-up":  lambda w, h: (0, h, w, 0),
    "h-rev":    lambda w, h: (w, 0, 0, 0),
}


def build_svg(frames, cols, stops, cycle, mode, gradient="h",
              fit_width=True,
              font_size=14, char_w=8.4, line_h=14, pad=6):
    rows = len(frames[0])
    w = round(cols * char_w, 2)
    h = rows * line_h + pad * 2
    grad = "".join(
        f'<stop offset="{(0 if len(stops) == 1 else i/(len(stops)-1)):.4f}" '
        f'stop-color="{c}"/>' for i, c in enumerate(stops))
    x1, y1, x2, y2 = GRADIENTS[gradient](w, h)

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
        f'width="{w}" height="{h}" role="img" '
        f'aria-label="Animated ASCII automaton banner">',
        f'<defs><linearGradient id="g" gradientUnits="userSpaceOnUse" '
        f'x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}">{grad}</linearGradient></defs>',
        "<style>text{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,"
        f'"DejaVu Sans Mono",monospace;font-size:{font_size}px;'
        "fill:url(#g);white-space:pre;text-rendering:optimizeSpeed}"
        "</style>",
    ]

    tl = (f' textLength="{w}" lengthAdjust="spacing"' if fit_width else "")

    def row_tag(i, line, extra=""):
        y = round(pad + (i + 1) * line_h - line_h * 0.22, 2)
        return (f'<text x="0" y="{y}"{tl} '
                f'xml:space="preserve"{extra}>{esc(line)}</text>')

    if mode == "frames" and len(frames) > 1:
        n = len(frames)
        kt = ";".join(f"{i/n:.4f}" for i in range(n))
        for fi, lines in enumerate(frames):
            vals = ";".join("inline" if j == fi else "none"
                            for j in range(n))
            out.append('<g display="none">')
            for i, line in enumerate(lines):
                out.append(row_tag(i, line))
            out.append(f'<animate attributeName="display" values="{vals}" '
                       f'keyTimes="{kt}" calcMode="discrete" dur="{cycle}s" '
                       f'repeatCount="indefinite"/></g>')
    elif mode == "cascade":
        lines = frames[0]
        for i, line in enumerate(lines):
            t0 = round(i * 0.60 / max(rows - 1, 1), 4)
            t1 = round(min(t0 + 0.03, 0.919), 4)
            anim = (f'<animate attributeName="opacity" values="0;0;1;1;0" '
                    f'keyTimes="0;{t0};{t1};0.92;1" dur="{cycle}s" '
                    f'repeatCount="indefinite"/>')
            out.append(row_tag(i, line, ' opacity="0"')
                       .replace("</text>", anim + "</text>"))
    else:
        for i, line in enumerate(frames[0]):
            out.append(row_tag(i, line))

    out.append("</svg>")
    return "".join(out)


# --------------------------------------------------------------------- main

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--automaton", default="110",
                   help="elementary rule number, a life-like name "
                        "(life, anneal, diamoeba, maze...), brain, or cyclic")
    p.add_argument("--cols", type=int, default=150)
    p.add_argument("--rows", type=int, default=30)
    p.add_argument("--seed", type=int, default=7)
    p.add_argument("--density", type=float, default=0.45)
    p.add_argument("--states", type=int, default=8, help="cyclic CA states")
    p.add_argument("--warmup", type=int, default=8,
                   help="generations to run before the first frame")
    p.add_argument("--single-seed", action="store_true")
    p.add_argument("--text-seed", action="store_true",
                   help="2D only: start from the wordmark and let it evolve")
    p.add_argument("--mode", default="frames",
                   choices=["frames", "cascade", "static"])
    p.add_argument("--frames", type=int, default=6)
    p.add_argument("--step", type=int, default=1)
    p.add_argument("--cycle", type=float, default=6.0)
    p.add_argument("--ramp", default=RAMP)
    p.add_argument("--colors", nargs="+",
                   default=["#22D3EE", "#818CF8", "#C084FC", "#F472B6"])
    p.add_argument("--text", default="")
    p.add_argument("--font", default="block", choices=list(FONTS))
    p.add_argument("--text-mode", default="solid",
                   choices=["off", "knockout", "solid", "outline"])
    p.add_argument("--italic", type=float, default=0.0)
    p.add_argument("--bold", action="store_true")
    p.add_argument("--no-halo", action="store_true")
    p.add_argument("--text-y", type=int, default=0)
    p.add_argument("--scale-x", type=int, default=None)
    p.add_argument("--scale-y", type=int, default=None)
    p.add_argument("--gradient", default="h", choices=list(GRADIENTS),
                   help="h, v, diag (top-left to bottom-right), "
                        "diag-up, h-rev")
    p.add_argument("--no-fit-width", action="store_true",
                   help="drop textLength; much faster to render")
    p.add_argument("--out", default="hero.svg")
    a = p.parse_args()

    nframes = a.frames if a.mode == "frames" else 1

    mask, outline = set(), set()
    if a.text and a.text_mode != "off":
        mask, outline = build_mask(a.text, a.cols, a.rows, a.font,
                                   a.scale_x, a.scale_y, a.italic,
                                   a.bold, a.text_y)

    is_1d = a.automaton.isdigit()
    frames = []

    if is_1d:
        rule = int(a.automaton)
        total = a.rows + (nframes - 1) * a.step
        grid = A.elementary(rule, a.cols, total, a.seed, a.single_seed)
        for f in range(nframes):
            win = grid[f * a.step: f * a.step + a.rows]
            frames.append(render_1d(win, a.ramp))
        label = f"rule {rule} ({A.ELEMENTARY.get(rule, '1D')})"
    else:
        name = a.automaton
        seed_mask = mask if (a.text_seed and mask) else None
        if name == "cyclic":
            r = random.Random(a.seed)
            g = [[r.randrange(a.states) for _ in range(a.cols)]
                 for _ in range(a.rows)]
            stepper = lambda G: A.step_cyclic(G, a.states)
            kind = "cyclic"
            label = f"cyclic CA, {a.states} states"
        elif name == "brain":
            g = A.seed_grid(a.cols, a.rows, a.seed, a.density, seed_mask)
            g = [[2 if c else 0 for c in row] for row in g]
            stepper = A.step_brain
            kind = "brain"
            label = "Brian's brain"
        else:
            spec, note = A.LIFELIKE[name]
            b, s = A.parse_bs(spec)
            g = A.seed_grid(a.cols, a.rows, a.seed, a.density, seed_mask)
            stepper = lambda G: A.step_lifelike(G, b, s)
            kind = "life"
            label = f"{name} {spec} ({note})"

        for _ in range(a.warmup):
            g = stepper(g)
        for f in range(nframes):
            frames.append(render_2d(g, a.ramp, kind, a.states))
            for _ in range(a.step):
                g = stepper(g)

    frames = [apply_mask(fr, mask, outline, a.text_mode, a.ramp,
                         not a.no_halo) for fr in frames]

    svg = build_svg(frames, a.cols, a.colors, a.cycle, a.mode, a.gradient,
                    not a.no_fit_width)
    with open(a.out, "w") as f:
        f.write(svg)
    print(f"{a.out}  {label}  {a.cols}x{a.rows}  "
          f"{nframes} frame(s)  {len(svg)/1024:.1f} KB")


if __name__ == "__main__":
    main()
