"""Write env.json (from env.py) into gridline-command.html.

usage: python3 integrate_env.py <game.html> <env.json>
Replaces everything between the 'environment models' markers (inserted on the first run before the resource models).
"""
import sys, json
game_path, json_path = sys.argv[1], sys.argv[2]
src = open(game_path, encoding='utf-8').read()
data = json.load(open(json_path))
START = '/* ---- environment models (Blender, art/env/env.py) ---- */\n'
END = '/* ---- end environment models ---- */\n'
code = START + """/* Low-poly scenery and resources authored in Blender, packed like the unit models:
   ENV_MODELS[name][piece] = {p:pivot, m:{material:base64 int16 triangles}}; materials come from ENV_PAL. */
const ENV_MODELS=""" + json.dumps(data['models'], separators=(',', ':')) + """;
const ENV_PAL=""" + json.dumps(data['palette'], separators=(',', ':')) + """;
const ENV_MATS={}, envGeoCache={};
for(const k in ENV_PAL) ENV_MATS[k]=new THREE.MeshLambertMaterial({color:new THREE.Color(ENV_PAL[k])});
ENV_MATS.lit.emissive.setHex(0xb08a3a); ENV_MATS.glass.emissive.setHex(0x22404c);   // lamps and windows glow a little
function envGeo(name,piece,mat){
  const ck=name+'|'+piece+'|'+mat;
  if(!envGeoCache[ck]){
    const bin=atob(ENV_MODELS[name][piece].m[mat]), u8=new Uint8Array(bin.length);
    for(let i=0;i<bin.length;i++) u8[i]=bin.charCodeAt(i);
    const i16=new Int16Array(u8.buffer), pos=new Float32Array(i16.length);
    for(let i=0;i<i16.length;i++) pos[i]=i16[i]/8192;
    const geo=new THREE.BufferGeometry(); geo.setAttribute('position',new THREE.BufferAttribute(pos,3)); geo.computeVertexNormals();
    geo.userData.keep=true;   // shared by every tile, so never disposed with one
    envGeoCache[ck]=geo;
  }
  return envGeoCache[ck];
}
/* a model as a group (animated pieces become child groups found in userData[piece]) */
/* team: the material that replaces the 'team' colour (a city's owner) */
function envModel(name, shadow=true, team=null){
  const g=new THREE.Group();
  for(const piece in ENV_MODELS[name]){
    const pd=ENV_MODELS[name][piece];
    let holder=g;
    if(piece!=='main'){ holder=new THREE.Group(); holder.position.fromArray(pd.p); g.add(holder); g.userData[piece]=holder; }
    for(const mat in pd.m){ const m=new THREE.Mesh(envGeo(name,piece,mat), mat==='team'&&team?team:ENV_MATS[mat]); m.castShadow=shadow; m.receiveShadow=true; holder.add(m); }
  }
  return g;
}
/* drop a static model straight into a tile group as loose meshes, so the tile's static merge can batch them */
function envPlace(g, name, x, y, z, rot=0, sc=1, shadow=true, team=null){
  const tmp=envModel(name, shadow, team); tmp.position.set(x,y,z); tmp.rotation.y=rot; tmp.scale.setScalar(sc); tmp.updateMatrix();
  for(const m of [...tmp.children]){ m.applyMatrix4(tmp.matrix); g.add(m); }
}
""" + END
if START in src:
    i, j = src.index(START), src.index(END)+len(END)
    src = src[:i]+code+src[j:]
else:
    anchor = '/* ---- resource models ---- */'
    assert anchor in src
    src = src.replace(anchor, code+anchor, 1)
open(game_path, 'w', encoding='utf-8').write(src)
print('integrated', len(code), 'bytes')
