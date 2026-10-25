"""
Operation Foothold — low-poly unit models (Polytopia-inspired), built procedurally in Blender.

Run:  python units.py <out_dir> [render]
Geometry is authored in GAME space (x right, y up, +z = facing direction, ground at y=0),
the same convention as the three.js code, then converted to Blender's Z-up on build.

Materials named 'body' and 'trim' are faction-colour placeholders; the game recolours them.
Sub-objects named 'rotor', 'tailRotor', 'radar' are separate pieces the game animates.
"""
import bpy, bmesh, math, sys, os, json, base64, struct
from contextlib import contextmanager
from mathutils import Vector, Matrix

PI = math.pi
OUT = sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else (sys.argv[1] if len(sys.argv) > 1 else 'out')
DO_RENDER = 'render' in sys.argv or 'quick' in sys.argv or 'heroes' in sys.argv
HEROES_ONLY = 'heroes' in sys.argv
QUICK = 'quick' in sys.argv
os.makedirs(OUT, exist_ok=True)

# ------------------------------------------------------------------ palette
PALETTE = {
    'body':    0x5aa7e8, 'trim':    0x2a5d96,           # faction placeholders (Aegis)
    'dark':    0x2c3136, 'rubber':  0x1f2326, 'metal':   0x4f585f, 'steel':  0x8a959c,
    'skin':    0xf2b98f, 'black':   0x16181b, 'glass':   0x9fdcf2, 'light':  0xfff1a8,
    'wood':    0x8f5d38, 'brass':   0xf2c14e, 'white':   0xeceff1, 'red':    0xe2483b,
    'leaf':    0x6f9140, 'leaf2':   0x4e6e2d, 'canvas':  0x7d7a52,
}
MATLIST = list(PALETTE.keys())
FACTIONS = {
    'aegis':   (0x5aa7e8, 0x2a5d96),
    'crimson': (0xe8625a, 0x8e3a35),
    'solaris': (0xf0b35c, 0xa67424),
    'ghost':   (0xb18ae8, 0x6f4fa8),
}

def lin(c):
    return c/12.92 if c <= 0.04045 else ((c+0.055)/1.055)**2.4
def rgba(h):
    return (lin((h >> 16 & 255)/255), lin((h >> 8 & 255)/255), lin((h & 255)/255), 1.0)

# ------------------------------------------------------------------ math helpers
def euler3(rx, ry, rz):
    """three.js Euler 'XYZ' (R = Rx·Ry·Rz)"""
    return Matrix.Rotation(rx, 4, 'X') @ Matrix.Rotation(ry, 4, 'Y') @ Matrix.Rotation(rz, 4, 'Z')
def T(v):
    return Matrix.Translation(Vector(v))
def S(v):
    return Matrix.Diagonal((v[0], v[1], v[2], 1.0))
Z2Y = Matrix.Rotation(-PI/2, 4, 'X')          # bmesh primitives are Z-aligned; make them Y-up
G2B = Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))  # game -> blender

# ------------------------------------------------------------------ model builder
class Model:
    def __init__(self, key):
        self.key = key
        self.buckets = {'main': {'pivot': Vector((0, 0, 0)), 'parts': []}}
        self.cur = 'main'
        self.stack = [Matrix.Identity(4)]

    @contextmanager
    def at(self, loc=(0, 0, 0), rot=(0, 0, 0)):
        self.stack.append(self.stack[-1] @ T(loc) @ euler3(*rot))
        yield
        self.stack.pop()

    @contextmanager
    def sub(self, name, pivot):
        """separate animated piece; contents are authored relative to its pivot"""
        wp = self.stack[-1] @ Vector(pivot)
        self.buckets[name] = {'pivot': wp, 'parts': []}
        prev, prevstack = self.cur, self.stack
        self.cur, self.stack = name, [Matrix.Identity(4)]
        yield
        self.cur, self.stack = prev, prevstack

    # -- core: finish a primitive bmesh (already scaled), bevel, colour, place
    def _finish(self, bm, mat, loc, rot, bevel, bseg, ang):
        if bevel > 0:
            edges = [e for e in bm.edges if e.is_manifold and e.calc_face_angle(0) > math.radians(ang)]
            if edges:
                bmesh.ops.bevel(bm, geom=edges, offset=bevel, offset_type='OFFSET', segments=bseg,
                                profile=0.5, affect='EDGES', clamp_overlap=True)
        mi = MATLIST.index(mat)
        for f in bm.faces:
            f.material_index = mi
        bmesh.ops.transform(bm, matrix=self.stack[-1] @ T(loc) @ euler3(*rot), verts=bm.verts)
        self.buckets[self.cur]['parts'].append(bm)

    def box(self, w, h, d, mat, loc=(0, 0, 0), rot=(0, 0, 0), bevel=0.012, bseg=1, taper=None):
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.transform(bm, matrix=S((w, h, d)), verts=bm.verts)
        if taper:   # (top_w_scale, top_d_scale, top_z_shift): wedge / tapered block
            for v in bm.verts:
                if v.co.y > 0:
                    v.co.x *= taper[0]; v.co.z = v.co.z*taper[1] + taper[2]
        self._finish(bm, mat, loc, rot, min(bevel, w*0.45, h*0.45, d*0.45), bseg, 40)

    def cyl(self, rt, rb, h, mat, loc=(0, 0, 0), rot=(0, 0, 0), seg=8, bevel=0.0, bseg=1):
        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=seg,
                              radius1=rb, radius2=max(rt, 0.0005), depth=h)
        bmesh.ops.transform(bm, matrix=Z2Y, verts=bm.verts)
        self._finish(bm, mat, loc, rot, bevel, bseg, max(55, 360/seg + 5))

    def cone(self, r, h, mat, loc=(0, 0, 0), rot=(0, 0, 0), seg=8):
        self.cyl(0.0, r, h, mat, loc, rot, seg)

    def sph(self, r, mat, loc=(0, 0, 0), rot=(0, 0, 0), seg=8, rings=6, scale=(1, 1, 1)):
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=rings, radius=r)
        bmesh.ops.transform(bm, matrix=S(scale) @ Z2Y, verts=bm.verts)
        self._finish(bm, mat, loc, rot, 0, 1, 90)

    def ico(self, r, mat, loc=(0, 0, 0), rot=(0, 0, 0), sub=1, scale=(1, 1, 1)):
        bm = bmesh.new()
        bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=r)
        bmesh.ops.transform(bm, matrix=S(scale), verts=bm.verts)
        self._finish(bm, mat, loc, rot, 0, 1, 90)

    def limb(self, p0, p1, w, mat, h=None, bevel=0.008, round_=False, seg=6):
        """a block (or rod) spanning p0 -> p1"""
        p0, p1 = Vector(p0), Vector(p1)
        d = p1 - p0
        q = Vector((0, 0, 1)).rotation_difference(d.normalized())
        e = q.to_euler('XYZ')
        # build in local frame then orient: easier to do the matrix directly
        bm = bmesh.new()
        if round_:
            bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=seg,
                                  radius1=w/2, radius2=w/2, depth=d.length)
        else:
            bmesh.ops.create_cube(bm, size=1.0)
            bmesh.ops.transform(bm, matrix=S((w, h or w, d.length)), verts=bm.verts)
            if bevel > 0:
                edges = [ed for ed in bm.edges if ed.calc_face_angle(0) > math.radians(40)]
                bmesh.ops.bevel(bm, geom=edges, offset=min(bevel, w*0.4), offset_type='OFFSET',
                                segments=1, profile=0.5, affect='EDGES', clamp_overlap=True)
        mi = MATLIST.index(mat)
        for f in bm.faces:
            f.material_index = mi
        M = self.stack[-1] @ T((p0+p1)/2) @ q.to_matrix().to_4x4()
        bmesh.ops.transform(bm, matrix=M, verts=bm.verts)
        self.buckets[self.cur]['parts'].append(bm)

    # -- build blender objects
    def build(self, collection, offset=(0, 0, 0)):
        root = bpy.data.objects.new(self.key, None)
        collection.objects.link(root)
        root.location = G2B @ Vector(offset)
        objs = {}
        for name, b in self.buckets.items():
            bm = bmesh.new()
            for part in b['parts']:
                vmap = {}
                for v in part.verts:
                    vmap[v] = bm.verts.new(G2B @ v.co)   # sub-piece parts are already pivot-relative
                for f in part.faces:
                    nf = bm.faces.new([vmap[v] for v in f.verts])
                    nf.material_index = f.material_index
            me = bpy.data.meshes.new(f'{self.key}_{name}')
            bm.to_mesh(me); bm.free()
            for m in MATLIST:
                me.materials.append(MATS[m])
            ob = bpy.data.objects.new(f'{self.key}_{name}', me)
            collection.objects.link(ob)
            ob.parent = root
            ob.location = G2B @ b['pivot'] if name != 'main' else (0, 0, 0)
            objs[name] = ob
        return root, objs

    def tri_count(self):
        n = 0
        for b in self.buckets.values():
            for p in b['parts']:
                n += sum(len(f.verts)-2 for f in p.faces)
        return n

    def export(self):
        """compact game format: per piece, per material, non-indexed triangles as int16 (1/8192 units)"""
        out = {}
        for name, b in self.buckets.items():
            per = {}
            for part in b['parts']:
                for f in part.faces:
                    vs = [v.co for v in f.verts]
                    m = MATLIST[f.material_index]
                    lst = per.setdefault(m, [])
                    for i in range(1, len(vs)-1):           # fan triangulation (faces are convex)
                        for v in (vs[0], vs[i], vs[i+1]):
                            lst += [round(c*8192) for c in v]
            out[name] = {
                'p': [round(c, 4) for c in b['pivot']] if name != 'main' else [0, 0, 0],
                'm': {m: base64.b64encode(struct.pack(f'<{len(a)}h', *a)).decode() for m, a in per.items()},
            }
        return out


# ================================================================== UNIT DESIGNS
def eyes(m, y, z, squint=False, gap=0.04):
    for s in (-1, 1):
        m.box(0.024, 0.012 if squint else 0.03, 0.01, 'black', (gap*s, y, z), bevel=0.003)


def infantry():
    m = Model('INF')
    for s in (-1, 1):
        m.box(0.066, 0.045, 0.088, 'dark', (0.046*s, 0.0225, 0.01), bevel=0.012)       # boots
        m.box(0.058, 0.06, 0.062, 'body', (0.046*s, 0.07, 0), bevel=0.01)             # stubby legs
    m.box(0.16, 0.15, 0.12, 'body', (0, 0.17, 0), bevel=0.022)                        # torso
    m.box(0.172, 0.085, 0.132, 'trim', (0, 0.19, 0), bevel=0.018)                     # flak vest
    m.box(0.168, 0.026, 0.128, 'dark', (0, 0.112, 0), bevel=0.006)                    # belt
    m.box(0.03, 0.022, 0.012, 'brass', (0, 0.112, 0.066), bevel=0.003)                # buckle
    for s in (-1, 1):
        m.box(0.04, 0.042, 0.02, 'dark', (0.045*s, 0.165, 0.072), bevel=0.006)        # pouches
    m.box(0.12, 0.13, 0.065, 'canvas', (0, 0.195, -0.09), bevel=0.018)                # backpack
    m.cyl(0.026, 0.026, 0.14, 'leaf2', (0, 0.275, -0.09), (0, 0, PI/2), seg=8)        # bedroll
    # big head + face
    m.box(0.17, 0.15, 0.15, 'skin', (0, 0.325, 0.005), bevel=0.032, bseg=2)
    eyes(m, 0.325, 0.083)
    # round helmet with brim and strap
    m.sph(0.108, 'trim', (0, 0.392, 0), seg=10, rings=8, scale=(1, 0.58, 1.04))
    m.cyl(0.114, 0.114, 0.016, 'trim', (0, 0.364, 0.004), seg=10)
    m.box(0.012, 0.06, 0.012, 'dark', (0.088, 0.33, 0.0), bevel=0)
    m.box(0.012, 0.06, 0.012, 'dark', (-0.088, 0.33, 0.0), bevel=0)
    # rifle held across the chest, muzzle up and to the side
    with m.at((0.0, 0.205, 0.105), (0, 0, 0.6)):
        m.box(0.2, 0.046, 0.036, 'metal', (0.02, 0, 0), bevel=0.008)
        m.box(0.085, 0.058, 0.034, 'wood', (-0.115, -0.01, 0), bevel=0.01)
        m.cyl(0.011, 0.011, 0.12, 'dark', (0.175, 0.006, 0), (0, 0, PI/2), seg=6)
        m.box(0.03, 0.06, 0.028, 'dark', (0.035, -0.045, 0), (0, 0, -0.25), bevel=0.006)
        m.box(0.07, 0.03, 0.04, 'wood', (0.1, -0.012, 0), bevel=0.008)                # handguard
    # arms reaching the rifle + hands
    m.limb((-0.098, 0.235, 0.0), (-0.045, 0.172, 0.105), 0.05, 'body')
    m.limb((0.098, 0.235, 0.0), (0.075, 0.255, 0.11), 0.05, 'body')
    m.box(0.045, 0.045, 0.045, 'skin', (-0.042, 0.172, 0.112), bevel=0.012)
    m.box(0.045, 0.045, 0.045, 'skin', (0.072, 0.252, 0.118), bevel=0.012)
    return m


def sniper():
    m = Model('SNP')
    # kneeling: right shin flat on the ground, left knee raised
    m.limb((0.05, 0.03, 0.0), (0.05, 0.03, -0.13), 0.062, 'body')
    m.box(0.064, 0.05, 0.05, 'dark', (0.05, 0.03, -0.165), bevel=0.01)
    m.limb((0.05, 0.03, 0.0), (0.05, 0.115, -0.03), 0.066, 'body')
    m.limb((-0.05, 0.115, -0.03), (-0.05, 0.135, 0.085), 0.066, 'body')
    m.limb((-0.05, 0.135, 0.085), (-0.05, 0.03, 0.095), 0.06, 'body')
    m.box(0.066, 0.045, 0.092, 'dark', (-0.05, 0.022, 0.11), bevel=0.012)
    # torso leaning into the shot, draped in a ghillie cape
    m.box(0.15, 0.14, 0.115, 'body', (0, 0.185, -0.01), (0.15, 0, 0), bevel=0.022)
    m.box(0.172, 0.13, 0.12, 'leaf', (0, 0.205, -0.035), (0.15, 0, 0), bevel=0.03, bseg=2)
    for p, r, mt in [((0.085, 0.255, -0.05), 0.042, 'leaf2'), ((-0.08, 0.25, -0.06), 0.04, 'leaf'),
                     ((0.0, 0.265, -0.09), 0.044, 'leaf2'), ((0.06, 0.17, -0.09), 0.036, 'leaf'),
                     ((-0.065, 0.16, -0.085), 0.034, 'leaf2'), ((0.0, 0.2, -0.105), 0.035, 'leaf')]:
        m.ico(r, mt, p, scale=(1, 0.8, 1))
    # head, squinting eyes, boonie hat in faction colours
    m.box(0.16, 0.14, 0.14, 'skin', (0, 0.315, 0.02), bevel=0.03, bseg=2)
    eyes(m, 0.318, 0.092, squint=True)
    m.cyl(0.125, 0.125, 0.014, 'trim', (0, 0.375, 0.02), seg=10)
    m.cyl(0.074, 0.086, 0.06, 'trim', (0, 0.405, 0.02), seg=10)
    m.cyl(0.088, 0.088, 0.016, 'dark', (0, 0.385, 0.02), seg=10)
    m.ico(0.02, 'leaf', (0.07, 0.4, -0.02))                                           # foliage in the hat band
    # long scoped rifle shouldered along +z
    X = -0.045
    m.box(0.036, 0.065, 0.1, 'wood', (X, 0.24, 0.0), bevel=0.01)
    m.box(0.042, 0.048, 0.17, 'metal', (X, 0.255, 0.12), bevel=0.008)
    m.cyl(0.012, 0.012, 0.27, 'dark', (X, 0.262, 0.335), (PI/2, 0, 0), seg=6)
    m.cyl(0.021, 0.021, 0.045, 'dark', (X, 0.262, 0.47), (PI/2, 0, 0), seg=8)
    m.cyl(0.026, 0.026, 0.13, 'dark', (X, 0.305, 0.125), (PI/2, 0, 0), seg=8)        # big scope
    m.cyl(0.031, 0.026, 0.03, 'dark', (X, 0.305, 0.2), (PI/2, 0, 0), seg=8)
    m.cyl(0.024, 0.024, 0.006, 'glass', (X, 0.305, 0.216), (PI/2, 0, 0), seg=8)
    for z in (0.09, 0.16):
        m.box(0.014, 0.03, 0.014, 'dark', (X, 0.282, z), bevel=0)
    m.box(0.03, 0.06, 0.03, 'dark', (X, 0.215, 0.1), (0.3, 0, 0), bevel=0.006)        # magazine
    for s in (-1, 1):                                                                 # bipod
        m.limb((X, 0.25, 0.36), (X+0.04*s, 0.005, 0.38), 0.012, 'dark', bevel=0)
    # arms + hands
    m.limb((-0.085, 0.235, 0.0), (X, 0.235, 0.07), 0.048, 'body')
    m.limb((0.085, 0.235, 0.0), (X+0.02, 0.232, 0.19), 0.048, 'body')
    m.box(0.044, 0.044, 0.044, 'skin', (X, 0.232, 0.075), bevel=0.012)
    m.box(0.044, 0.044, 0.044, 'skin', (X+0.015, 0.232, 0.2), bevel=0.012)
    return m


def tank():
    m = Model('TNK')
    for s in (-1, 1):
        m.box(0.13, 0.13, 0.62, 'rubber', (0.2*s, 0.068, 0), bevel=0.05, bseg=2)    # tracks
        for i in range(4):
            m.cyl(0.046, 0.046, 0.02, 'metal', (0.268*s, 0.064, -0.21+i*0.14), (0, 0, PI/2), seg=8)
            m.cyl(0.018, 0.018, 0.024, 'steel', (0.27*s, 0.064, -0.21+i*0.14), (0, 0, PI/2), seg=6)
        m.cyl(0.05, 0.05, 0.022, 'steel', (0.27*s, 0.085, 0.27), (0, 0, PI/2), seg=8)
        m.cyl(0.05, 0.05, 0.022, 'steel', (0.27*s, 0.085, -0.27), (0, 0, PI/2), seg=8)
        m.box(0.155, 0.022, 0.66, 'trim', (0.2*s, 0.145, 0), bevel=0.008)            # fenders
        m.box(0.04, 0.03, 0.02, 'light', (0.12*s, 0.225, 0.3), bevel=0.006)          # headlights
        m.cyl(0.036, 0.036, 0.09, 'metal', (0.12*s, 0.255, -0.27), (0, 0, PI/2), seg=8)  # fuel drums
    m.box(0.36, 0.12, 0.56, 'body', (0, 0.19, -0.01), bevel=0.03)                     # hull
    m.box(0.34, 0.03, 0.15, 'trim', (0, 0.22, 0.27), (0.5, 0, 0), bevel=0.01)          # glacis plate
    # chunky turret
    m.box(0.29, 0.12, 0.3, 'trim', (0, 0.31, -0.03), bevel=0.045, bseg=2)
    m.box(0.21, 0.04, 0.2, 'body', (0, 0.382, -0.05), bevel=0.015)
    m.cyl(0.05, 0.055, 0.03, 'metal', (0.055, 0.41, -0.09), seg=8)                     # hatch
    m.box(0.045, 0.03, 0.03, 'glass', (-0.06, 0.405, 0.02), bevel=0.006)               # periscope
    m.box(0.12, 0.09, 0.06, 'metal', (0, 0.31, 0.14), bevel=0.018)                     # mantlet
    m.cyl(0.032, 0.036, 0.3, 'metal', (0, 0.315, 0.3), (PI/2, 0, 0), seg=8)            # barrel
    m.cyl(0.046, 0.046, 0.065, 'dark', (0, 0.315, 0.46), (PI/2, 0, 0), seg=8, bevel=0.008)
    m.box(0.09, 0.05, 0.06, 'wood', (0, 0.32, -0.21), bevel=0.01)                      # stowage crate
    m.cyl(0.005, 0.005, 0.22, 'dark', (-0.1, 0.48, -0.13), seg=4)                       # antenna
    m.box(0.004, 0.05, 0.075, 'body', (-0.1, 0.565, -0.172), bevel=0)                    # pennant
    return m


def artillery():
    m = Model('ART')
    for s in (-1, 1):
        m.cyl(0.135, 0.135, 0.07, 'rubber', (0.2*s, 0.135, 0.02), (0, 0, PI/2), seg=12, bevel=0.018)
        m.cyl(0.085, 0.085, 0.074, 'trim', (0.2*s, 0.135, 0.02), (0, 0, PI/2), seg=12)
        m.cyl(0.032, 0.032, 0.086, 'steel', (0.2*s, 0.135, 0.02), (0, 0, PI/2), seg=6)
        m.limb((0.065*s, 0.16, -0.06), (0.16*s, 0.035, -0.42), 0.055, 'body')        # split trails
        m.box(0.085, 0.075, 0.022, 'dark', (0.165*s, 0.04, -0.44), bevel=0.006)       # spades
    m.cyl(0.02, 0.02, 0.38, 'dark', (0, 0.135, 0.02), (0, 0, PI/2), seg=6)            # axle
    m.box(0.22, 0.09, 0.24, 'body', (0, 0.185, 0.0), bevel=0.022)                          # carriage
    m.box(0.42, 0.2, 0.03, 'trim', (0, 0.27, 0.12), (-0.15, 0, 0), bevel=0.014)      # gun shield
    m.box(0.08, 0.06, 0.035, 'trim', (0.17, 0.38, 0.11), (-0.15, 0, 0), bevel=0.012)
    m.box(0.08, 0.06, 0.035, 'trim', (-0.17, 0.38, 0.11), (-0.15, 0, 0), bevel=0.012)
    with m.at((0, 0.27, 0.02), (-0.6, 0, 0)):                                           # elevated gun
        m.box(0.13, 0.1, 0.24, 'metal', (0, 0, 0), bevel=0.02)
        m.cyl(0.054, 0.06, 0.18, 'body', (0, 0.0, 0.16), (PI/2, 0, 0), seg=8, bevel=0.01)
        m.cyl(0.034, 0.04, 0.38, 'metal', (0, 0, 0.4), (PI/2, 0, 0), seg=8)
        m.cyl(0.052, 0.052, 0.07, 'dark', (0, 0, 0.6), (PI/2, 0, 0), seg=8, bevel=0.01)
        m.box(0.1, 0.1, 0.08, 'dark', (0, 0, -0.14), bevel=0.014)
    # ammo crate + shells between the trails
    m.box(0.11, 0.06, 0.13, 'wood', (0, 0.03, -0.22), bevel=0.01)
    for i in range(3):
        x = -0.03 + 0.03*i
        m.cyl(0.014, 0.014, 0.07, 'brass', (x, 0.095, -0.22), seg=8)
        m.cone(0.014, 0.03, 'dark', (x, 0.145, -0.22), seg=8)
    return m


def flak():
    m = Model('AA')
    m.box(0.3, 0.06, 0.62, 'dark', (0, 0.1, 0), bevel=0.01)                              # chassis
    for s in (-1, 1):
        for z in (0.2, -0.07, -0.21):
            m.cyl(0.066, 0.066, 0.05, 'rubber', (0.17*s, 0.066, z), (0, 0, PI/2), seg=10, bevel=0.012)
            m.cyl(0.028, 0.028, 0.056, 'steel', (0.17*s, 0.066, z), (0, 0, PI/2), seg=6)
        m.box(0.075, 0.022, 0.17, 'trim', (0.17*s, 0.142, 0.2), bevel=0.006)            # fenders
        m.box(0.075, 0.022, 0.3, 'trim', (0.17*s, 0.142, -0.14), bevel=0.006)
        m.box(0.04, 0.03, 0.015, 'light', (0.09*s, 0.165, 0.352), bevel=0.005)          # headlights
        m.box(0.012, 0.045, 0.08, 'glass', (0.142*s, 0.235, 0.205), bevel=0)             # side windows
        m.box(0.05, 0.05, 0.07, 'leaf2', (0.12*s, 0.205, -0.27), bevel=0.008)           # ammo cans
    m.box(0.28, 0.14, 0.16, 'body', (0, 0.205, 0.205), bevel=0.03, bseg=2)               # cab
    m.box(0.24, 0.07, 0.08, 'body', (0, 0.165, 0.31), bevel=0.02)                        # hood
    m.box(0.16, 0.035, 0.012, 'dark', (0, 0.155, 0.351), bevel=0.003)                    # grille
    m.box(0.22, 0.05, 0.012, 'glass', (0, 0.24, 0.287), (-0.25, 0, 0), bevel=0)          # windshield
    m.box(0.3, 0.05, 0.36, 'body', (0, 0.155, -0.13), bevel=0.015)                       # flatbed
    m.cyl(0.12, 0.13, 0.05, 'trim', (0, 0.205, -0.13), seg=10)                           # turret ring
    m.box(0.06, 0.05, 0.05, 'dark', (0, 0.26, -0.25), bevel=0.01)                         # gunner seat
    with m.at((0, 0.27, -0.12), (-0.9, 0, 0)):                                            # quad autocannon
        m.box(0.18, 0.08, 0.13, 'metal', (0, 0, 0), bevel=0.016)
        for s in (-1, 1):
            m.box(0.02, 0.11, 0.15, 'trim', (0.1*s, 0, -0.01), bevel=0.006)
        for xo in (-0.06, -0.025, 0.025, 0.06):
            m.cyl(0.012, 0.014, 0.28, 'dark', (xo, 0, 0.2), (PI/2, 0, 0), seg=6)
            m.cyl(0.018, 0.018, 0.04, 'dark', (xo, 0, 0.35), (PI/2, 0, 0), seg=6)
    m.cyl(0.008, 0.008, 0.1, 'dark', (0.08, 0.325, 0.18), seg=5)                          # radar mast
    with m.sub('radar', (0.08, 0.38, 0.18)):
        m.box(0.14, 0.055, 0.014, 'steel', (0, 0, 0), (0.2, 0, 0), bevel=0.005)
        m.cyl(0.004, 0.004, 0.035, 'dark', (0, 0, 0.02), (PI/2, 0, 0), seg=4)
        m.sph(0.009, 'red', (0, 0, 0.04), seg=6, rings=4)
    return m


def helicopter():
    m = Model('HEL')
    m.box(0.24, 0.2, 0.36, 'body', (0, 0.22, 0.02), bevel=0.07, bseg=2)                 # chubby fuselage
    m.box(0.2, 0.14, 0.13, 'body', (0, 0.2, 0.2), bevel=0.05, bseg=2)                    # nose
    m.sph(0.1, 'glass', (0, 0.28, 0.13), seg=10, rings=6, scale=(0.95, 0.78, 1.15))       # bubble canopy
    m.sph(0.036, 'dark', (0, 0.13, 0.24), seg=8, rings=6)                                 # chin turret
    m.cyl(0.009, 0.009, 0.09, 'dark', (0, 0.125, 0.3), (PI/2, 0, 0), seg=6)
    m.box(0.14, 0.06, 0.19, 'trim', (0, 0.34, -0.05), bevel=0.025)                        # engine hump
    for s in (-1, 1):
        m.cyl(0.02, 0.024, 0.04, 'dark', (0.055*s, 0.34, -0.155), (PI/2, 0, 0), seg=8)   # exhausts
        m.box(0.15, 0.022, 0.075, 'trim', (0.17*s, 0.2, 0.0), bevel=0.008)               # stub wings
        m.cyl(0.031, 0.031, 0.12, 'metal', (0.225*s, 0.172, 0.0), (PI/2, 0, 0), seg=8, bevel=0.006)
        m.cyl(0.024, 0.024, 0.006, 'red', (0.225*s, 0.172, 0.062), (PI/2, 0, 0), seg=8)   # rocket pod face
        m.cyl(0.011, 0.011, 0.42, 'dark', (0.11*s, 0.028, 0.02), (PI/2, 0, 0), seg=6)     # skids
        m.limb((0.11*s, 0.028, 0.23), (0.11*s, 0.06, 0.27), 0.022, 'dark', round_=True)
        for z in (0.1, -0.08):
            m.limb((0.11*s, 0.03, z), (0.075*s, 0.14, z), 0.018, 'dark', round_=True)
    m.cyl(0.055, 0.035, 0.32, 'trim', (0, 0.25, -0.3), (PI/2, 0, 0), seg=8)               # tail boom
    m.box(0.022, 0.14, 0.085, 'body', (0, 0.31, -0.46), (-0.3, 0, 0), bevel=0.008)        # fin
    m.box(0.19, 0.016, 0.06, 'body', (0, 0.255, -0.41), bevel=0.005)                      # stabiliser
    with m.sub('tailRotor', (0.024, 0.33, -0.48)):
        m.cyl(0.016, 0.016, 0.02, 'metal', (0, 0, 0), (0, 0, PI/2), seg=6)
        m.box(0.006, 0.16, 0.026, 'dark', (0.006, 0, 0), bevel=0)
        m.box(0.006, 0.026, 0.16, 'dark', (0.006, 0, 0), bevel=0)
    m.cyl(0.022, 0.022, 0.06, 'dark', (0, 0.395, -0.01), seg=6)                           # rotor mast
    with m.sub('rotor', (0, 0.43, -0.01)):
        m.cyl(0.036, 0.036, 0.03, 'metal', (0, 0, 0), seg=8)
        m.box(0.05, 0.01, 0.86, 'dark', (0, 0.008, 0), bevel=0)
        m.box(0.86, 0.01, 0.05, 'dark', (0, 0.008, 0), bevel=0)
        for x, z in ((0, 0.405), (0, -0.405), (0.405, 0), (-0.405, 0)):
            m.box(0.053 if x == 0 else 0.05, 0.013, 0.05 if x == 0 else 0.053, 'brass', (x, 0.008, z), bevel=0)
    return m


def nuke():
    m = Model('NUKE')
    m.box(0.32, 0.06, 0.64, 'dark', (0, 0.1, -0.01), bevel=0.01)                          # chassis
    for s in (-1, 1):
        for z in (0.22, 0.08, -0.11, -0.25):
            m.cyl(0.062, 0.062, 0.05, 'rubber', (0.175*s, 0.062, z), (0, 0, PI/2), seg=10, bevel=0.012)
            m.cyl(0.026, 0.026, 0.056, 'steel', (0.175*s, 0.062, z), (0, 0, PI/2), seg=6)
        m.box(0.04, 0.03, 0.015, 'light', (0.095*s, 0.18, 0.302), bevel=0.005)
        m.box(0.012, 0.045, 0.07, 'glass', (0.152*s, 0.235, 0.23), bevel=0)
        m.limb((0.07*s, 0.15, -0.02), (0.05*s, 0.27, -0.13), 0.03, 'metal', round_=True)   # erector rams
    m.box(0.3, 0.13, 0.14, 'body', (0, 0.205, 0.23), bevel=0.03, bseg=2)                  # cab
    m.box(0.22, 0.05, 0.012, 'glass', (0, 0.24, 0.297), (-0.2, 0, 0), bevel=0)
    m.box(0.3, 0.04, 0.42, 'trim', (0, 0.15, -0.09), bevel=0.012)                         # launcher bed
    # warning placard on the cab nose
    m.box(0.075, 0.075, 0.01, 'brass', (0, 0.18, 0.302), bevel=0.004)
    m.cyl(0.022, 0.022, 0.012, 'black', (0, 0.18, 0.306), (PI/2, 0, 0), seg=3)
    with m.at((0, 0.21, -0.3), (-0.8, 0, 0)):                                               # raised missile
        m.box(0.11, 0.04, 0.46, 'metal', (0, -0.085, 0.21), bevel=0.012)                    # launch rail
        m.cyl(0.068, 0.068, 0.4, 'white', (0, 0, 0.23), (PI/2, 0, 0), seg=10)
        m.cyl(0.07, 0.07, 0.04, 'trim', (0, 0, 0.13), (PI/2, 0, 0), seg=10)
        m.cyl(0.07, 0.07, 0.03, 'black', (0, 0, 0.34), (PI/2, 0, 0), seg=10)
        m.cone(0.068, 0.15, 'red', (0, 0, 0.505), (PI/2, 0, 0), seg=10)
        m.cyl(0.048, 0.06, 0.035, 'dark', (0, 0, 0.012), (PI/2, 0, 0), seg=10)              # nozzle
        for i in range(4):
            a = i*PI/2 + PI/4
            m.box(0.014, 0.1, 0.1, 'trim', (math.sin(a)*0.09, math.cos(a)*0.09, 0.075), (0, 0, -a), bevel=0.005)
        m.box(0.004, 0.06, 0.06, 'brass', (0.069, 0, 0.24), bevel=0)                         # trefoil decal
        m.cyl(0.017, 0.017, 0.006, 'black', (0.072, 0, 0.24), (0, 0, PI/2), seg=3)
    return m


UNITS = [infantry, sniper, tank, artillery, flak, helicopter, nuke]

# ================================================================== scene / render
bpy.ops.wm.read_factory_settings(use_empty=True)
MATS = {}
for name, hexc in PALETTE.items():
    mt = bpy.data.materials.new(name)
    try:
        mt.use_nodes = True
    except Exception:
        pass
    bsdf = mt.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = rgba(hexc)
    bsdf.inputs['Roughness'].default_value = 0.08 if name == 'glass' else 0.75
    if name in ('metal', 'steel'):
        bsdf.inputs['Metallic'].default_value = 0.35
    if name == 'light':
        bsdf.inputs['Emission Color'].default_value = rgba(0xfff1a8)
        bsdf.inputs['Emission Strength'].default_value = 1.5
    mt.diffuse_color = rgba(hexc)
    MATS[name] = mt
tile_mat = bpy.data.materials.new('tile'); tile_mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = rgba(0x4d6a45)
tile_mat.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.9
side_mat = bpy.data.materials.new('tileside'); side_mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = rgba(0x35492f)

scn = bpy.context.scene
col = scn.collection
models = [f() for f in UNITS]

stats = {}
export = {}
for i, mdl in enumerate(models):
    stats[mdl.key] = mdl.tri_count()
    export[mdl.key] = mdl.export()
with open(os.path.join(OUT, 'units.json'), 'w') as fh:
    json.dump(export, fh, separators=(',', ':'))
print('triangles:', stats, 'json bytes:', os.path.getsize(os.path.join(OUT, 'units.json')))

def tile(x):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.transform(bm, matrix=T((0, 0, -0.06)) @ S((0.96, 0.96, 0.12)), verts=bm.verts)
    edges = [e for e in bm.edges]
    bmesh.ops.bevel(bm, geom=edges, offset=0.02, segments=1, profile=0.5, affect='EDGES', clamp_overlap=True)
    for f in bm.faces:
        f.material_index = 0 if f.normal.z > 0.9 else 1
    me = bpy.data.meshes.new('tile'); bm.to_mesh(me)
    me.materials.append(tile_mat); me.materials.append(side_mat)
    ob = bpy.data.objects.new('tile', me); col.objects.link(ob)
    ob.location = (x, 0, 0)
    return ob

if DO_RENDER:
    SP = 1.05
    placed = []
    for i, mdl in enumerate(models):
        x = (i-(len(models)-1)/2)*SP
        root, objs = mdl.build(col, (x, 0, 0))
        tob = tile(x)
        root.rotation_euler.z = math.radians(32)   # three-quarter pose for the lineup
        if mdl.key == 'HEL':
            root.location.z += 0.32        # hover above its tile (game flies helis higher)
        placed.append((mdl.key, x, root, [tob, root] + list(objs.values())))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'units.blend'))

    # light rig: warm key sun from the game's sun direction + cool sky fill
    sun = bpy.data.lights.new('sun', 'SUN'); sun.energy = 4.0; sun.angle = math.radians(12)
    sun.color = (1.0, 0.95, 0.87)
    so = bpy.data.objects.new('sun', sun); col.objects.link(so)
    so.rotation_euler = (Vector((8, -6, 14)).to_track_quat('Z', 'Y')).to_euler()
    world = bpy.data.worlds.new('w'); scn.world = world
    bg = world.node_tree.nodes['Background']
    bg.inputs['Color'].default_value = (0.32, 0.38, 0.36, 1); bg.inputs['Strength'].default_value = 1.25

    scn.render.engine = 'CYCLES'
    scn.cycles.device = 'CPU'
    scn.cycles.samples = 24 if QUICK else 96
    scn.cycles.use_denoising = True
    scn.render.film_transparent = True
    scn.view_settings.view_transform = 'Standard'
    scn.render.image_settings.file_format = 'PNG'
    scn.render.image_settings.color_mode = 'RGBA'

    cam_d = bpy.data.cameras.new('cam')
    cam = bpy.data.objects.new('cam', cam_d); col.objects.link(cam); scn.camera = cam

    def aim(target, az, el, dist):
        t = Vector(target)
        p = t + Vector((math.sin(az)*math.cos(el), -math.cos(az)*math.cos(el), math.sin(el)))*dist
        cam.location = p
        cam.rotation_euler = (t-p).to_track_quat('-Z', 'Y').to_euler()

    def set_faction(fk):
        b, t = FACTIONS[fk]
        for nm, h in (('body', b), ('trim', t)):
            MATS[nm].node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = rgba(h)

    # lineup per faction
    cam_d.type = 'ORTHO'; cam_d.ortho_scale = 7.7
    scn.render.resolution_x, scn.render.resolution_y = 2200, 620
    for fk in ([] if HEROES_ONLY else ['aegis'] if QUICK else FACTIONS):
        set_faction(fk)
        aim((0, 0, 0.2), 0, math.radians(30), 20)
        scn.render.filepath = os.path.join(OUT, f'lineup_{fk}.png')
        bpy.ops.render.render(write_still=True)

    if QUICK:
        sys.exit(0)
    # hero close-ups (Aegis), front three-quarter + rear three-quarter
    set_faction('aegis')
    cam_d.type = 'PERSP'; cam_d.lens = 60
    scn.render.resolution_x, scn.render.resolution_y = 900, 900
    for key, x, root, mine in placed:
        root.rotation_euler.z = 0
        for _, _, _, other in placed:
            for ob in other:
                ob.hide_render = other is not mine
        tz = {'HEL': 0.6, 'INF': 0.2, 'SNP': 0.19}.get(key, 0.22)
        dist = {'INF': 1.45, 'SNP': 1.6, 'HEL': 2.25}.get(key, 1.95)
        for tag, az in (('front', 35), ('back', 215)):
            aim((x, 0, tz), math.radians(az), math.radians(24), dist)
            scn.render.filepath = os.path.join(OUT, f'unit_{key}_{tag}.png')
            bpy.ops.render.render(write_still=True)
print('done')
