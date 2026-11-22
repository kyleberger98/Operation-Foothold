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


MODELS = [pine('PINE'), pine('PINE2', tiers=2, h=0.4, r=0.15, cols=('pine2', 'pine')), pine('FIR', tiers=4, h=0.54, r=0.14, cols=('pine3', 'pine', 'pine2')),
          broadleaf('OAK'), bush('BUSH'), mountain('MTN1', 1), mountain('MTN2', 7), boulders('ROCKS'),
          crop('CROP'), ore('ORE'), pumpjack('PUMP'), oilrig('RIG'), supplydrop('DROP')]

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
        x = (i % 7-3)*1.1; z = (i//7)*1.2
        root, objs = mdl.build(col, (x, 0, z))
        bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0); bmesh.ops.transform(bm, matrix=T((0, 0, -0.06)) @ S((0.96, 0.96, 0.12)), verts=bm.verts)
        me = bpy.data.meshes.new('t'); bm.to_mesh(me); me.materials.append(tile_mat); ob = bpy.data.objects.new('t', me); col.objects.link(ob); ob.location = G2B @ Vector((x, 0, z))
    sun = bpy.data.lights.new('sun', 'SUN'); sun.energy = 4; so = bpy.data.objects.new('sun', sun); col.objects.link(so)
    so.rotation_euler = (Vector((8, -6, 14)).to_track_quat('Z', 'Y')).to_euler()
    w = bpy.data.worlds.new('w'); scn.world = w; w.use_nodes = True; w.node_tree.nodes['Background'].inputs['Strength'].default_value = 1.2
    scn.render.engine = 'CYCLES'; scn.cycles.samples = 48; scn.cycles.use_denoising = True; scn.render.film_transparent = True
    scn.render.resolution_x, scn.render.resolution_y = 1800, 700
    cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = 8.6; cam = bpy.data.objects.new('c', cd); col.objects.link(cam); scn.camera = cam
    t = Vector((0, -0.6, 0.2)); p = t+Vector((0, -math.cos(0.55), math.sin(0.55)))*20; cam.location = p; cam.rotation_euler = (t-p).to_track_quat('-Z', 'Y').to_euler()
    scn.render.filepath = os.path.join(OUT, 'env_lineup.png'); bpy.ops.render.render(write_still=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'env.blend'))
print('done')
