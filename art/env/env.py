"""
Gridline Command - low-poly environment and resource models, built procedurally in Blender.

Run:  python env.py <out_dir> [render]
Reuses the modelling helpers from ../units/units.py (same conventions: game space, y up, ground at y=0,
one tile is 1 x 1). Exports env.json for integrate_env.py.
"""
import os, sys, math, json
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, '..', 'units', 'units.py'), encoding='utf-8').read()
exec(src.split('# ================================================================== UNIT DESIGNS')[0])   # Model, helpers, PALETTE

# environment palette (game recolours none of these)
PALETTE.clear()
PALETTE.update({
    'trunk': 0x5a4430, 'bark': 0x463422, 'pine': 0x2f5f36, 'pine2': 0x3b7343, 'pine3': 0x24502c,
    'leaf': 0x4f8a3e, 'leaf2': 0x3c7232, 'leafY': 0x7aa443,
    'rock': 0x77818a, 'rock2': 0x5d666e, 'rockD': 0x48505a, 'snow': 0xe3ecf0,
    'wheat': 0xd9b65a, 'wheat2': 0xc39b42, 'soil': 0x6d5236, 'hay': 0xe0c06a,
    'wood': 0x8f5d38, 'woodD': 0x6a4428, 'metal': 0x4f585f, 'steel': 0x8a959c, 'dark': 0x2c3136,
    'ore': 0xe3a344, 'oreG': 0x7fd0c0, 'red': 0xd8483b, 'white': 0xeceff1, 'yellow': 0xf2c94c,
    'canvas': 0xe9e4d4, 'oil': 0x1d1f22, 'grass': 0x5f8f48,
    # cities: 'team' is swapped in game for the owner's colour (grey while neutral)
    'team': 0x4f86c6, 'wall': 0xe2d9c6, 'wall2': 0xb7bec4, 'wall3': 0xcfa98a, 'glass': 0x86bfd6, 'lit': 0xffd98e,
    'pave': 0x9a958a, 'pave2': 0x7e796f, 'stone': 0x9d978c, 'roofG': 0x5d646b,
    # shores
    'reed': 0x6b9440, 'cattail': 0x6a4a2c, 'lily': 0x4f9a4a, 'pink': 0xf2a7c8,
    # theme scenery (unlocked board themes)
    'palm': 0x8a6a44, 'palmD': 0x6e5234, 'frond': 0x3f9a46, 'frond2': 0x2f7f3a, 'coco': 0x5a3a20,
    'cactus': 0x4f8a4a, 'cactusD': 0x3c6f3a, 'flower': 0xf06a8a, 'charred': 0x2a2422, 'ember': 0xff7a2a,
    'drift': 0xf2f6f8, 'gold': 0xe8b84a, 'goldD': 0xb08428, 'pole': 0x3a3f44,
})
MATLIST[:] = list(PALETTE.keys())


def pine(key, tiers=3, h=0.46, r=0.16, cols=('pine', 'pine2', 'pine3')):
    m = Model(key)
    m.cyl(0.026, 0.034, h*0.3, 'trunk', (0, h*0.15, 0), seg=6)
    for i in range(tiers):
        t = i/tiers
        rr = r*(1-t*0.55)
        hh = h*0.42*(1-t*0.25)
        y = h*0.22 + i*h*0.24
        m.cyl(0.0, rr, hh, cols[i % len(cols)], (0, y+hh/2, 0), (0, i*0.6, 0), seg=7)
    return m


def broadleaf(key):
    m = Model(key)
    m.cyl(0.03, 0.042, 0.2, 'bark', (0, 0.1, 0), seg=6)
    m.limb((0, 0.16, 0), (0.07, 0.26, 0.02), 0.03, 'bark', round_=True)
    m.limb((0, 0.16, 0), (-0.06, 0.25, -0.03), 0.028, 'bark', round_=True)
    for p, r, c in [((0, 0.33, 0), 0.13, 'leaf'), ((0.08, 0.29, 0.04), 0.1, 'leaf2'), ((-0.08, 0.28, -0.03), 0.1, 'leaf2'),
                    ((0.02, 0.27, -0.09), 0.09, 'leafY'), ((-0.02, 0.4, 0.03), 0.08, 'leafY')]:
        m.ico(r, c, p, sub=1, scale=(1, 0.85, 1))
    return m


def bush(key):
    m = Model(key)
    for p, r, c in [((0, 0.05, 0), 0.07, 'leaf2'), ((0.06, 0.04, 0.03), 0.05, 'leaf'), ((-0.05, 0.035, -0.02), 0.045, 'leafY')]:
        m.ico(r, c, p, sub=1, scale=(1, 0.75, 1))
    return m


def mountain(key, seed):
    m = Model(key)
    import random
    R = random.Random(seed)
    # main peak: a 6-sided cone, a lower shoulder, rubble around the foot
    m.cyl(0.0, 0.42, 0.62, 'rock', (0, 0.31, 0), (0, R.random(), 0), seg=6)
    m.cyl(0.0, 0.2, 0.2, 'snow', (0, 0.555, 0), (0, R.random(), 0), seg=6)
    m.cyl(0.0, 0.27, 0.36, 'rock2', (0.22, 0.18, -0.16), (0, R.random(), 0), seg=5)
    m.cyl(0.0, 0.1, 0.1, 'snow', (0.22, 0.31, -0.16), (0, R.random(), 0), seg=5)
    m.cyl(0.0, 0.2, 0.26, 'rockD', (-0.24, 0.13, 0.12), (0, R.random(), 0), seg=5)
    for _ in range(4):
        a = R.random()*math.tau
        d = 0.32+R.random()*0.08
        m.ico(0.035+R.random()*0.03, 'rock2', (math.cos(a)*d, 0.025, math.sin(a)*d), sub=0)
    return m


def boulders(key):
    m = Model(key)
    m.ico(0.06, 'rock', (0, 0.035, 0), sub=0, scale=(1.2, 0.8, 1))
    m.ico(0.035, 'rock2', (0.07, 0.02, 0.03), sub=0)
    return m


def crop(key):
    """Wheat field: furrowed soil, rows of wheat clumps, a haystack and a fence post."""
    m = Model(key)
    m.box(0.8, 0.02, 0.8, 'soil', (0, 0.01, 0), bevel=0.006)
    for row in range(4):
        z = -0.3+row*0.2
        m.box(0.74, 0.012, 0.05, 'woodD', (0, 0.026, z+0.08), bevel=0.002)            # furrow
        for i in range(6):
            x = -0.3+i*0.12+((row % 2)*0.05)
            if row == 0 and i >= 4:
                continue                                                           # room for the haystack
            # a wheat clump: a bundle of stalks topped with a fat golden head
            m.cyl(0.018, 0.012, 0.07, 'grass', (x, 0.055, z), seg=5)
            m.ico(0.034, 'wheat' if (i+row) % 2 else 'wheat2', (x, 0.105, z), sub=0, scale=(0.9, 1.5, 0.9))
    m.cyl(0.0, 0.11, 0.16, 'hay', (0.24, 0.1, -0.28), seg=8)                         # haystack
    m.cyl(0.11, 0.11, 0.05, 'hay', (0.24, 0.03, -0.28), seg=8)
    m.box(0.02, 0.12, 0.02, 'wood', (-0.37, 0.07, 0.37), bevel=0.003)                # fence post
    return m


def ore(key):
    """Ore deposit: faceted rocks with glinting copper and teal veins, a pickaxe and a small mine cart."""
    m = Model(key)
    m.ico(0.17, 'rock2', (-0.08, 0.1, 0.04), sub=0, scale=(1.1, 0.8, 1))
    m.ico(0.12, 'rock', (0.14, 0.07, -0.1), sub=0)
    m.ico(0.08, 'rockD', (-0.22, 0.05, -0.16), sub=0)
    for p, s, c in [((-0.05, 0.19, 0.06), 0.045, 'ore'), ((0.0, 0.15, 0.15), 0.035, 'ore'), ((0.12, 0.15, -0.06), 0.035, 'oreG'),
                    ((-0.16, 0.12, 0.02), 0.03, 'ore'), ((0.18, 0.1, -0.16), 0.028, 'oreG')]:
        m.ico(s, c, p, sub=0)                                                      # veins / crystals
    with m.at((0.2, 0.0, 0.2), (0, 0.6, 0)):                                       # mine cart on a rail stub
        m.box(0.05, 0.008, 0.26, 'metal', (0.05, 0.006, 0), bevel=0)
        m.box(0.05, 0.008, 0.26, 'metal', (-0.05, 0.006, 0), bevel=0)
        m.box(0.12, 0.07, 0.15, 'woodD', (0, 0.06, 0), bevel=0.01)
        m.ico(0.035, 'ore', (0, 0.1, 0.02), sub=0)
        m.ico(0.03, 'rock2', (0.03, 0.1, -0.03), sub=0)
        for sx in (-1, 1):
            for sz in (-1, 1):
                m.cyl(0.018, 0.018, 0.012, 'dark', (0.065*sx, 0.02, 0.05*sz), (0, 0, PI/2), seg=6)
    with m.at((-0.2, 0.0, 0.22), (0, -0.5, 0.35)):                                 # pickaxe leaning on a rock
        m.limb((0, 0.0, 0), (0, 0.16, 0), 0.012, 'wood', round_=True)
        m.box(0.12, 0.014, 0.014, 'steel', (0, 0.16, 0), bevel=0.003)
    return m


def pumpjack(key):
    """Oil pumpjack with a rocking beam (piece 'beam', pivot on the samson post), barrels and a tank."""
    m = Model(key)
    m.box(0.42, 0.03, 0.18, 'dark', (0, 0.015, 0), bevel=0.006)                     # skid
    m.limb((-0.03, 0.03, 0.05), (0.0, 0.27, 0.0), 0.022, 'yellow')                 # samson post (A-frame)
    m.limb((-0.03, 0.03, -0.05), (0.0, 0.27, 0.0), 0.022, 'yellow')
    m.limb((0.05, 0.03, 0.0), (0.0, 0.27, 0.0), 0.02, 'yellow')
    m.box(0.08, 0.07, 0.07, 'metal', (-0.16, 0.065, 0), bevel=0.01)                 # motor
    m.cyl(0.04, 0.04, 0.03, 'dark', (-0.1, 0.09, 0.045), (PI/2, 0, 0), seg=8)       # crank wheel
    m.cyl(0.015, 0.015, 0.1, 'steel', (0.2, 0.08, 0), seg=6)                         # wellhead
    m.box(0.05, 0.03, 0.05, 'red', (0.2, 0.03, 0), bevel=0.005)
    for i, (x, z) in enumerate([(-0.28, 0.22), (-0.2, 0.27), (-0.3, 0.3)]):
        m.cyl(0.035, 0.035, 0.09, 'red' if i % 2 else 'metal', (x, 0.045, z), seg=8)  # oil drums
    m.cyl(0.07, 0.07, 0.16, 'steel', (0.26, 0.08, 0.24), seg=10)                    # storage tank
    m.cyl(0.072, 0.072, 0.012, 'dark', (0.26, 0.165, 0.24), seg=10)
    with m.sub('beam', (0.0, 0.28, 0.0)):
        m.box(0.46, 0.035, 0.04, 'yellow', (0.0, 0.0, 0), bevel=0.006)
        m.box(0.06, 0.11, 0.05, 'dark', (0.24, -0.02, 0), bevel=0.01)              # horse head
        m.box(0.1, 0.1, 0.07, 'metal', (-0.21, -0.03, 0), bevel=0.01)               # counterweight
        m.limb((0.26, -0.07, 0), (0.24, -0.2, 0), 0.008, 'dark', round_=True)       # bridle down to the well
    return m


def oilrig(key):
    """Offshore oil rig: legs into the sea, a deck with a lattice derrick, crane, helipad and a flare."""
    m = Model(key)
    for sx in (-1, 1):
        for sz in (-1, 1):
            m.cyl(0.028, 0.034, 0.36, 'metal', (0.17*sx, -0.06, 0.17*sz), seg=6)
            m.limb((0.17*sx, -0.1, 0.17*sz), (0.0, 0.0, 0.17*sz), 0.012, 'metal', round_=True)
    m.box(0.52, 0.05, 0.52, 'dark', (0, 0.12, 0), bevel=0.01)                        # deck
    m.box(0.5, 0.012, 0.5, 'steel', (0, 0.15, 0), bevel=0)
    # derrick: four tapered legs and cross bars
    for sx in (-1, 1):
        for sz in (-1, 1):
            m.limb((0.07*sx, 0.15, 0.07*sz), (0.015*sx, 0.5, 0.015*sz), 0.012, 'red', round_=True)
    for y in (0.24, 0.34, 0.43):
        w = 0.07-(y-0.15)*0.16
        m.box(w*2, 0.008, 0.008, 'red', (0, y, w), bevel=0)
        m.box(w*2, 0.008, 0.008, 'red', (0, y, -w), bevel=0)
    m.box(0.13, 0.08, 0.12, 'white', (0.15, 0.2, 0.14), bevel=0.01)                 # living quarters
    m.box(0.13, 0.02, 0.12, 'red', (0.15, 0.25, 0.14), bevel=0)
    m.cyl(0.08, 0.08, 0.012, 'yellow', (-0.16, 0.16, 0.16), seg=10)                 # helipad
    m.cyl(0.06, 0.06, 0.014, 'dark', (-0.16, 0.162, 0.16), seg=10)
    m.limb((-0.17, 0.15, -0.17), (-0.05, 0.32, -0.28), 0.014, 'yellow', round_=True)  # crane boom
    m.limb((0.2, 0.15, -0.2), (0.3, 0.36, -0.3), 0.01, 'steel', round_=True)        # flare boom
    m.cone(0.025, 0.06, 'ore', (0.3, 0.38, -0.3), seg=5)                           # flame
    return m


def supplydrop(key):
    """Supply drop: a banded crate with a parachute canopy draped beside it."""
    m = Model(key)
    m.box(0.28, 0.2, 0.28, 'wood', (0, 0.1, 0), bevel=0.02)
    for y in (0.04, 0.16):
        m.box(0.29, 0.025, 0.29, 'dark', (0, y, 0), bevel=0.004)
    m.box(0.12, 0.003, 0.12, 'white', (0, 0.202, 0), bevel=0)                      # stencilled cross
    m.box(0.12, 0.004, 0.035, 'red', (0, 0.204, 0), bevel=0)
    m.box(0.035, 0.004, 0.12, 'red', (0, 0.204, 0), bevel=0)
    m.sph(0.2, 'canvas', (0.17, 0.02, -0.17), (0.4, 0.6, 1.2), seg=8, rings=4, scale=(1, 0.45, 1))  # collapsed canopy
    for dx in (-0.08, 0.08):
        m.limb((0.1+dx, 0.06, -0.1), (0.0, 0.18, 0.0), 0.005, 'dark', round_=True)  # shroud lines
    return m


def gable(m, w, d, h, mat, loc, rot=(0, 0, 0)):
    """pitched roof: a wedge running along x"""
    m.box(w, h, d, mat, loc, rot, bevel=0.004, taper=(1, 0.04, 0))


def windows(m, x0, x1, y0, rows, dy, z, n, mat='glass', ww=0.022, wh=0.03, face=1):
    """a grid of window panes on a wall facing +z (face=1) or +x (face=2)"""
    for r in range(rows):
        for i in range(n):
            t = (i+0.5)/n
            a = x0+(x1-x0)*t
            if face == 1:
                m.box(ww, wh, 0.006, mat, (a, y0+r*dy, z), bevel=0)
            else:
                m.box(0.006, wh, ww, mat, (z, y0+r*dy, a), bevel=0)


def plaza(key):
    m = Model(key)
    m.box(0.86, 0.014, 0.86, 'pave2', (0, 0.007, 0), bevel=0.004)
    m.box(0.8, 0.006, 0.8, 'pave', (0, 0.016, 0), bevel=0)
    for i in range(-3, 4):                     # paving joints
        m.box(0.8, 0.002, 0.008, 'pave2', (0, 0.0195, i*0.1), bevel=0)
    for x, z in [(-0.36, 0.36), (0.36, -0.36)]:
        m.cyl(0.04, 0.045, 0.03, 'stone', (x, 0.03, z), seg=8)      # planters
        m.ico(0.045, 'leaf', (x, 0.07, z), sub=1, scale=(1, 0.8, 1))
    for x, z in [(0.38, 0.38), (-0.38, -0.12)]:
        m.cyl(0.005, 0.006, 0.12, 'dark', (x, 0.08, z), seg=5)       # street lamps
        m.sph(0.014, 'lit', (x, 0.145, z), seg=6, rings=4)
    return m


def townhall(key):
    """level-1 city centre: a civic hall with columns, pediment and a clock tower"""
    m = Model(key)
    m.box(0.3, 0.025, 0.24, 'stone', (0, 0.0125, 0), bevel=0.005)    # plinth
    m.box(0.28, 0.17, 0.2, 'wall', (0, 0.11, -0.02), bevel=0.008)
    windows(m, -0.12, 0.12, 0.09, 2, 0.065, 0.081, 4, ww=0.03, wh=0.038)
    for i in range(4):
        m.cyl(0.011, 0.012, 0.15, 'white', (-0.09+i*0.06, 0.1, 0.105), seg=6)   # columns
    m.box(0.27, 0.02, 0.05, 'white', (0, 0.185, 0.1), bevel=0.003)
    gable(m, 0.3, 0.27, 0.08, 'team', (0, 0.235, 0))
    m.box(0.07, 0.12, 0.07, 'wall', (0, 0.31, -0.04), bevel=0.006)    # clock tower
    m.cyl(0.022, 0.022, 0.006, 'white', (0, 0.33, -0.004), (PI/2, 0, 0), seg=10)
    m.cyl(0.0, 0.06, 0.08, 'team', (0, 0.41, -0.04), (0, PI/4, 0), seg=4)
    m.box(0.05, 0.08, 0.008, 'woodD', (0, 0.065, 0.081), bevel=0)    # door
    return m


def hq(key):
    """capital: a stepped command headquarters with a comms mast, dish and beacon"""
    m = Model(key)
    m.box(0.38, 0.03, 0.32, 'stone', (0, 0.015, 0), bevel=0.006)
    m.box(0.34, 0.3, 0.26, 'wall2', (0, 0.18, -0.02), bevel=0.01)
    windows(m, -0.15, 0.15, 0.09, 4, 0.06, 0.111, 6, ww=0.032, wh=0.034)
    windows(m, -0.12, 0.08, 0.09, 4, 0.06, 0.171, 4, ww=0.03, wh=0.034, face=2)
    m.box(0.35, 0.03, 0.27, 'team', (0, 0.345, -0.02), bevel=0.006)   # coloured crown
    m.box(0.2, 0.12, 0.16, 'wall2', (-0.04, 0.42, -0.04), bevel=0.008)
    windows(m, -0.12, 0.04, 0.42, 1, 0, 0.041, 3, wh=0.05)
    m.box(0.21, 0.02, 0.17, 'team', (-0.04, 0.49, -0.04), bevel=0.004)
    m.cyl(0.007, 0.01, 0.26, 'dark', (-0.08, 0.63, -0.06), seg=5)      # mast
    m.sph(0.02, 'lit', (-0.08, 0.77, -0.06), seg=8, rings=5)
    m.sph(0.05, 'steel', (0.06, 0.53, -0.06), (0.9, 0.5, 0), seg=10, rings=4, scale=(1, 0.35, 1))   # dish
    m.box(0.12, 0.09, 0.012, 'glass', (0, 0.075, 0.112), bevel=0)     # glazed entrance
    m.box(0.16, 0.012, 0.05, 'team', (0, 0.125, 0.13), bevel=0.003)   # canopy
    return m


def house(key, two=False):
    m = Model(key)
    h = 0.15 if two else 0.09
    m.box(0.14, h, 0.12, 'wall3' if two else 'wall', (0, h/2, 0), bevel=0.006)
    windows(m, -0.05, 0.05, 0.05, 2 if two else 1, 0.06, 0.061, 2, ww=0.024, wh=0.026)
    m.box(0.03, 0.05, 0.006, 'woodD', (0.0 if two else 0.035, 0.025, 0.061), bevel=0)
    if two:
        m.box(0.155, 0.065, 0.135, 'team', (0, h+0.03, 0), bevel=0.006, taper=(0.55, 0.45, 0))   # hipped roof
    else:
        gable(m, 0.16, 0.14, 0.07, 'team', (0, h+0.035, 0))
    m.box(0.022, 0.05, 0.022, 'stone', (-0.04, h+0.05, -0.03), bevel=0.003)                     # chimney
    return m


def flats(key):
    m = Model(key)
    m.box(0.16, 0.24, 0.15, 'wall2', (0, 0.12, 0), bevel=0.008)
    windows(m, -0.06, 0.06, 0.05, 4, 0.052, 0.076, 3)
    windows(m, -0.055, 0.055, 0.05, 4, 0.052, 0.081, 3, face=2)
    m.box(0.17, 0.02, 0.16, 'team', (0, 0.25, 0), bevel=0.004)
    m.box(0.05, 0.03, 0.05, 'roofG', (0.03, 0.275, -0.03), bevel=0.004)
    return m


def tower(key):
    m = Model(key)
    m.box(0.15, 0.4, 0.15, 'glass', (0, 0.2, 0), bevel=0.006)
    for y in range(1, 8):
        m.box(0.155, 0.01, 0.155, 'wall2', (0, y*0.05, 0), bevel=0)  # floor bands
    m.box(0.12, 0.05, 0.12, 'team', (0, 0.425, 0), bevel=0.008)
    m.cyl(0.004, 0.006, 0.1, 'dark', (0.03, 0.5, 0.03), seg=5)
    return m


def citywalls(key):
    """city walls: a low crenellated ring round the tile with coloured corner towers and a gate at the front"""
    m = Model(key)
    R = 0.43
    for side in range(4):
        with m.at((0, 0, 0), (0, side*PI/2, 0)):
            segs = [(-0.3, -0.07), (0.07, 0.3)] if side == 0 else [(-0.3, 0.3)]
            for a, b in segs:
                m.box(b-a, 0.07, 0.035, 'stone', ((a+b)/2, 0.035, R), bevel=0)
                n = max(1, int((b-a)/0.05))
                for i in range(n):
                    m.box(0.022, 0.02, 0.04, 'stone', (a+(i+0.5)*(b-a)/n, 0.08, R), bevel=0)
    for sx in (-1, 1):
        for sz in (-1, 1):
            m.cyl(0.05, 0.055, 0.12, 'stone', (R*sx, 0.06, R*sz), seg=7)
            m.cyl(0.0, 0.065, 0.07, 'team', (R*sx, 0.155, R*sz), seg=7)
    for sx in (-1, 1):
        m.box(0.04, 0.11, 0.05, 'stone', (0.09*sx, 0.055, R), bevel=0.004)   # gatehouse
    m.box(0.22, 0.03, 0.05, 'team', (0, 0.12, R), bevel=0.004)
    return m


def reeds(key):
    m = Model(key)
    import random
    R = random.Random(3)
    for i in range(7):
        x, z = R.uniform(-0.06, 0.06), R.uniform(-0.05, 0.05)
        h = R.uniform(0.08, 0.15)
        m.limb((x, -0.02, z), (x+R.uniform(-0.015, 0.015), h, z), 0.008, 'reed', round_=True, seg=4)
        if i % 2 == 0:
            m.cyl(0.008, 0.008, 0.03, 'cattail', (x, h-0.01, z), seg=5)
    return m


def lilies(key):
    m = Model(key)
    for x, z, r in [(0, 0, 0.045), (0.07, 0.03, 0.035), (-0.04, 0.06, 0.03)]:
        m.cyl(r, r, 0.006, 'lily', (x, 0.003, z), seg=9)
    m.ico(0.016, 'pink', (0.005, 0.014, -0.004), sub=1, scale=(1, 0.7, 1))
    return m


def palm(key, lean=0.18, h=0.5, seed=1):
    """palm tree: a curved, ringed trunk, drooping fronds and a few coconuts"""
    import random
    R = random.Random(seed)
    m = Model(key)
    n = 6
    pts = [(lean*(i/n)**1.6, h*i/n, 0.0) for i in range(n+1)]
    for i in range(n):
        m.limb(pts[i], pts[i+1], 0.034-0.012*i/n, 'palm' if i % 2 else 'palmD', round_=True, seg=6)
    top = pts[-1]
    for k in range(7):
        a = k*math.tau/7+R.uniform(-0.2, 0.2)
        col = 'frond' if k % 2 else 'frond2'
        p = Vector(top)
        for L, d in [(0.12, 0.25), (0.11, 0.85)]:         # two segments: out, then drooping
            dirv = Vector((math.cos(a)*math.cos(d), -math.sin(d), -math.sin(a)*math.cos(d)))
            c = p+dirv*(L/2)
            m.sph(1.0, col, tuple(c), (0, a, -d), seg=6, rings=3, scale=(L/2, 0.008, 0.042))
            p = p+dirv*L*0.92
    for k in range(3):
        a = k*math.tau/3+0.4
        m.sph(0.018, 'coco', (top[0]+math.cos(a)*0.03, top[1]-0.03, top[2]+math.sin(a)*0.03), seg=6, rings=4)
    return m


def cactus(key):
    m = Model(key)
    m.cyl(0.03, 0.034, 0.2, 'cactus', (0, 0.1, 0), seg=7)
    m.sph(0.03, 'cactus', (0, 0.2, 0), seg=7, rings=4)
    for sx, y0, h in [(1, 0.08, 0.08), (-1, 0.11, 0.06)]:
        m.limb((0, y0, 0), (0.07*sx, y0, 0), 0.026, 'cactusD', round_=True, seg=6)
        m.cyl(0.02, 0.022, h, 'cactusD', (0.07*sx, y0+h/2, 0), seg=6)
        m.sph(0.02, 'cactusD', (0.07*sx, y0+h, 0), seg=6, rings=3)
    m.ico(0.014, 'flower', (0.005, 0.232, 0), sub=0)
    return m


def snowpine(key, tiers=3, h=0.46, r=0.16):
    """a pine weighed down with snow: dark tiers with white caps"""
    m = Model(key)
    m.cyl(0.026, 0.034, h*0.3, 'trunk', (0, h*0.15, 0), seg=6)
    for i in range(tiers):
        t = i/tiers
        rr = r*(1-t*0.55); hh = h*0.42*(1-t*0.25); y = h*0.22+i*h*0.24
        m.cyl(0.0, rr, hh, 'pine3' if i % 2 else 'pine', (0, y+hh/2, 0), (0, i*0.6, 0), seg=7)
        m.cyl(rr*0.42, rr*0.78, hh*0.22, 'snow', (0, y+hh*0.42, 0), (0, i*0.6, 0), seg=7)   # snow on the bough
    m.cyl(0.0, r*0.3, h*0.14, 'snow', (0, h*0.22+(tiers-1)*h*0.24+h*0.33, 0), seg=7)        # snowy tip
    return m


def deadtree(key, seed=2):
    """a charred, leafless tree with a glowing ember or two"""
    import random
    R = random.Random(seed)
    m = Model(key)
    m.limb((0, 0, 0), (0.02, 0.3, 0.01), 0.04, 'charred', round_=True, seg=6)
    for k in range(4):
        a = k*math.tau/4+R.uniform(-0.4, 0.4)
        y = R.uniform(0.14, 0.26); L = R.uniform(0.09, 0.14)
        p0 = (0.012, y, 0.006); p1 = (math.cos(a)*L, y+R.uniform(0.05, 0.1), math.sin(a)*L)
        m.limb(p0, p1, 0.018, 'charred', round_=True, seg=5)
        m.limb(p1, (p1[0]*1.3, p1[1]+0.05, p1[2]*1.3), 0.01, 'charred', round_=True, seg=4)
    m.ico(0.016, 'ember', (0.02, 0.06, 0.03), sub=0)
    m.ico(0.012, 'ember', (-0.03, 0.03, -0.02), sub=0)
    return m


def drift(key):
    m = Model(key)
    m.sph(0.08, 'drift', (0, 0.0, 0), seg=8, rings=4, scale=(1.4, 0.35, 1))
    m.sph(0.05, 'drift', (0.08, 0.0, 0.03), seg=8, rings=4, scale=(1.2, 0.4, 1))
    return m


def flagpole(key):
    """city flagpole: stone base, slim pole and a gold finial (the cloth is drawn in game)"""
    m = Model(key)
    m.cyl(0.04, 0.05, 0.03, 'stone', (0, 0.015, 0), seg=8)
    m.cyl(0.008, 0.011, 0.5, 'pole', (0, 0.28, 0), seg=8)
    m.cyl(0.016, 0.016, 0.012, 'goldD', (0, 0.53, 0), seg=8)
    m.sph(0.02, 'gold', (0, 0.555, 0), seg=8, rings=6)
    return m


MODELS = [pine('PINE'), pine('PINE2', tiers=2, h=0.4, r=0.15, cols=('pine2', 'pine')), pine('FIR', tiers=4, h=0.54, r=0.14, cols=('pine3', 'pine', 'pine2')),
          broadleaf('OAK'), bush('BUSH'), mountain('MTN1', 1), mountain('MTN2', 7), boulders('ROCKS'),
          crop('CROP'), ore('ORE'), pumpjack('PUMP'), oilrig('RIG'), supplydrop('DROP'),
          plaza('PLAZA'), townhall('HALL'), hq('HQ'), house('HOUSE'), house('HOUSE2', two=True), flats('FLATS'), tower('TOWER'),
          citywalls('WALLS'), reeds('REEDS'), lilies('LILY'),
          palm('PALM'), palm('PALM2', lean=-0.12, h=0.42, seed=5), cactus('CACTUS'), snowpine('SNOWPINE'), snowpine('SNOWFIR', tiers=4, h=0.54, r=0.14),
          deadtree('DEAD'), deadtree('DEAD2', seed=9), drift('DRIFT'), flagpole('POLE')]

OUT = sys.argv[1] if len(sys.argv) > 1 else 'out'
os.makedirs(OUT, exist_ok=True)
export = {m.key: m.export() for m in MODELS}
with open(os.path.join(OUT, 'env.json'), 'w') as fh:
    json.dump({'palette': {k: '#%06x' % v for k, v in PALETTE.items()}, 'models': export}, fh, separators=(',', ':'))
print('triangles:', {m.key: m.tri_count() for m in MODELS}, 'bytes:', os.path.getsize(os.path.join(OUT, 'env.json')))

if 'render' in sys.argv:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    MATS.clear() if 'MATS' in globals() else None
    globals()['MATS'] = {}
    for name, hexc in PALETTE.items():
        mt = bpy.data.materials.new(name); mt.use_nodes = True
        b = mt.node_tree.nodes.get('Principled BSDF'); b.inputs['Base Color'].default_value = rgba(hexc); b.inputs['Roughness'].default_value = 0.8
        MATS[name] = mt
    scn = bpy.context.scene; col = scn.collection
    tile_mat = bpy.data.materials.new('tile'); tile_mat.use_nodes = True; tile_mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = rgba(0x4d6a45)
    for i, mdl in enumerate(MODELS):
        x = (i % 8-3.5)*1.1; z = (i//8)*1.2
        root, objs = mdl.build(col, (x, 0, z))
        bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0); bmesh.ops.transform(bm, matrix=T((0, 0, -0.06)) @ S((0.96, 0.96, 0.12)), verts=bm.verts)
        me = bpy.data.meshes.new('t'); bm.to_mesh(me); me.materials.append(tile_mat); ob = bpy.data.objects.new('t', me); col.objects.link(ob); ob.location = G2B @ Vector((x, 0, z))
    sun = bpy.data.lights.new('sun', 'SUN'); sun.energy = 4; so = bpy.data.objects.new('sun', sun); col.objects.link(so)
    so.rotation_euler = (Vector((8, -6, 14)).to_track_quat('Z', 'Y')).to_euler()
    w = bpy.data.worlds.new('w'); scn.world = w; w.use_nodes = True; w.node_tree.nodes['Background'].inputs['Strength'].default_value = 1.2
    scn.render.engine = 'CYCLES'; scn.cycles.samples = 48; scn.cycles.use_denoising = True; scn.render.film_transparent = True
    scn.render.resolution_x, scn.render.resolution_y = 1800, 1000
    cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = 9.6; cam = bpy.data.objects.new('c', cd); col.objects.link(cam); scn.camera = cam
    t = Vector((0, -1.2, 0.2)); p = t+Vector((0, -math.cos(0.55), math.sin(0.55)))*20; cam.location = p; cam.rotation_euler = (t-p).to_track_quat('-Z', 'Y').to_euler()
    scn.render.filepath = os.path.join(OUT, 'env_lineup.png'); bpy.ops.render.render(write_still=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'env.blend'))
print('done')
