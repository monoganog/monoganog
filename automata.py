"""1D elementary and 2D cellular automata for the ASCII banner."""

import random

# ---------------------------------------------------------------- 1D rules

ELEMENTARY = {
    18: "sparse fractal", 22: "fine grain", 26: "thin diagonals",
    30: "chaotic", 45: "dense chaos", 54: "sparse lattice",
    60: "clean diagonal", 73: "boxed pockets", 90: "sierpinski nesting",
    105: "dense triangles", 106: "drifting diagonal", 110: "gliders",
    122: "mottled", 126: "broad triangles", 129: "inverse fractal",
    150: "dense weave", 154: "fine diagonal", 182: "heavy fill",
    188: "rightward drift", 190: "thick diagonal", 225: "growing chaos",
}

# ------------------------------------------- 2D life-like: B/S neighbour sets

LIFELIKE = {
    "life":        ("B3/S23",          "gliders, still lifes"),
    "highlife":    ("B36/S23",         "life plus replicators"),
    "daynight":    ("B3678/S34678",    "symmetric blobs"),
    "seeds":       ("B2/S",            "explosive, sparse"),
    "maze":        ("B3/S12345",       "growing corridors"),
    "mazectric":   ("B3/S1234",        "long straight corridors"),
    "coral":       ("B3/S45678",       "slow crystalline growth"),
    "anneal":      ("B4678/S35678",    "coalescing blobs"),
    "majority":    ("B45678/S5678",    "melting into pools"),
    "diamoeba":    ("B35678/S5678",    "amoeba, writhing edges"),
    "walledcities":("B45678/S2345",    "cells inside walls"),
    "gnarl":       ("B1/S1",           "fractal filigree"),
    "replicator":  ("B1357/S1357",     "self-copying"),
    "stains":      ("B3678/S235678",   "spreading stains"),
}

OTHER_2D = {
    "brain":  "Brian's brain — travelling wavefronts",
    "cyclic": "cyclic CA — spiral waves",
}


def parse_bs(spec):
    b, s = spec.split("/")
    birth = set(int(c) for c in b[1:])
    survive = set(int(c) for c in s[1:])
    return birth, survive


def rng(seed):
    return random.Random(seed)


# ---------------------------------------------------------------------- 1D

def elementary(rule, cols, gens, seed, single_seed=False):
    """Returns gens rows; row index is time."""
    if single_seed:
        row = [0] * cols
        row[cols // 2] = 1
    else:
        r = rng(seed)
        row = [r.randint(0, 1) for _ in range(cols)]
    grid = [row]
    for _ in range(gens - 1):
        p = grid[-1]
        grid.append([
            (rule >> ((p[(i - 1) % cols] << 2) | (p[i] << 1) | p[(i + 1) % cols])) & 1
            for i in range(cols)
        ])
    return grid


# ---------------------------------------------------------------------- 2D

def seed_grid(cols, rows, seed, density, mask=None):
    if mask is not None:
        return [[1 if (y, x) in mask else 0 for x in range(cols)]
                for y in range(rows)]
    r = rng(seed)
    return [[1 if r.random() < density else 0 for _ in range(cols)]
            for _ in range(rows)]


def neigh_count(g, y, x, rows, cols, val=1):
    n = 0
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dx == 0 and dy == 0:
                continue
            if g[(y + dy) % rows][(x + dx) % cols] == val:
                n += 1
    return n


def step_lifelike(g, birth, survive):
    rows, cols = len(g), len(g[0])
    out = []
    for y in range(rows):
        row = []
        for x in range(cols):
            n = neigh_count(g, y, x, rows, cols)
            alive = g[y][x]
            row.append(1 if ((alive and n in survive) or
                             (not alive and n in birth)) else 0)
        out.append(row)
    return out


def step_brain(g):
    """0 dead, 2 alive, 1 dying."""
    rows, cols = len(g), len(g[0])
    out = []
    for y in range(rows):
        row = []
        for x in range(cols):
            s = g[y][x]
            if s == 2:
                row.append(1)
            elif s == 1:
                row.append(0)
            else:
                row.append(2 if neigh_count(g, y, x, rows, cols, 2) == 2 else 0)
        out.append(row)
    return out


def step_cyclic(g, nstates, threshold=1):
    rows, cols = len(g), len(g[0])
    out = []
    for y in range(rows):
        row = []
        for x in range(cols):
            s = g[y][x]
            nxt = (s + 1) % nstates
            c = 0
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    if dx == 0 and dy == 0:
                        continue
                    if g[(y + dy) % rows][(x + dx) % cols] == nxt:
                        c += 1
            row.append(nxt if c >= threshold else s)
        out.append(row)
    return out
