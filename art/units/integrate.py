"""Swap the game's procedural unit builders for the Blender-made models.

usage: python3 integrate.py <game.html> <units.json>
Replaces everything between the 'unit model builders' marker and the 'HP/label sprite' marker.
"""
import sys, json, base64, struct

game_path, json_path = sys.argv[1], sys.argv[2]
src = open(game_path, encoding='utf-8').read()
models = json.load(open(json_path))

START = '/* ---- unit model builders ---- */\n'
END = '/* ---- HP/label sprite ---- */'
i, j = src.index(START), src.index(END)

def top(pieces):
    t = 0
    for p in pieces.values():
        for b in p['m'].values():
            raw = base64.b64decode(b)
            a = struct.unpack(f'<{len(raw)//2}h', raw)
            t = max(t, max(a[k]/8192 + p['p'][1] for k in range(1, len(a), 3)))
    return round(t, 3)
tops = {k: top(v) for k, v in models.items()}

code = START + """/* Low-poly unit models authored in Blender (art/units/units.py) and packed as
   int16 triangle soup: UNIT_MODELS[type][piece] = {p:pivot, m:{material:base64}}.
   'body'/'trim' take the faction colours; 'rotor', 'tailRotor' and 'radar' are
   separate pieces so the render loop can spin them. */
const UNIT_MODELS=""" + json.dumps(models, separators=(',', ':')) + """;
const UNIT_PAL={dark:0x2c3136, rubber:0x1f2326, metal:0x4f585f, steel:0x8a959c, skin:0xf2b98f, black:0x16181b,
  glass:0x9fdcf2, light:0xfff1a8, wood:0x8f5d38, brass:0xf2c14e, white:0xeceff1, red:0xe2483b,
  leaf:0x6f9140, leaf2:0x4e6e2d, canvas:0x7d7a52};
const UNIT_MATS={};
for(const k in UNIT_PAL) UNIT_MATS[k]=new THREE.MeshLambertMaterial(k==='light'?{color:UNIT_PAL[k],emissive:0x6b5a1e}:{color:UNIT_PAL[k]});
const unitGeoCache={};
function unitGeo(type,piece,mat){
  const ck=type+'|'+piece+'|'+mat;
  if(!unitGeoCache[ck]){
    const bin=atob(UNIT_MODELS[type][piece].m[mat]), u8=new Uint8Array(bin.length);
    for(let i=0;i<bin.length;i++) u8[i]=bin.charCodeAt(i);
    const i16=new Int16Array(u8.buffer), pos=new Float32Array(i16.length);
    for(let i=0;i<i16.length;i++) pos[i]=i16[i]/8192;
    const geo=new THREE.BufferGeometry();
    geo.setAttribute('position',new THREE.BufferAttribute(pos,3));
    geo.computeVertexNormals(); // non-indexed, so normals come out flat-shaded
    unitGeoCache[ck]=geo;
  }
  return unitGeoCache[ck];
}
function makeUnitModel(type,fm){
  const g=new THREE.Group();
  for(const piece in UNIT_MODELS[type]){
    const pd=UNIT_MODELS[type][piece];
    let holder=g;
    if(piece!=='main'){ holder=new THREE.Group(); holder.position.fromArray(pd.p); g.add(holder); g.userData[piece]=holder; }
    for(const mat in pd.m){
      const mesh=new THREE.Mesh(unitGeo(type,piece,mat), mat==='body'?fm.body:mat==='trim'?fm.trim:UNIT_MATS[mat]);
      mesh.castShadow=true; mesh.receiveShadow=true;
      holder.add(mesh);
    }
  }
  return g;
}
const UNIT_TOP=""" + json.dumps(tops, separators=(',', ':')) + """;   // model height, keeps the HP label clear of the unit
const BUILDERS=Object.fromEntries(Object.keys(UNIT_MODELS).map(k=>[k,fm=>makeUnitModel(k,fm)]));

"""
src = src[:i] + code + src[j:]
OLD_LBL = "lbl.position.y=(UNIT_TYPES[u.type].fly?0.95:0.72);"
NEW_LBL = "lbl.position.y=(UNIT_TYPES[u.type].fly?0.95:Math.max(0.72,(UNIT_TOP[u.type]||0)+0.12));"
if OLD_LBL in src:
    src = src.replace(OLD_LBL, NEW_LBL)
assert NEW_LBL in src
open(game_path, 'w', encoding='utf-8').write(src)
print('integrated', len(code), 'bytes of model code')
