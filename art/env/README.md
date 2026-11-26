# Environment and resource models

Made in Blender by `env.py` (low-poly, flat colours, same pipeline as `art/units`).

| Model | Used for |
|---|---|
| PINE, PINE2, FIR, OAK, BUSH | Forest tiles (mixed per tile) |
| MTN1, MTN2 | Mountain tiles |
| ROCKS | Scattered boulders on plains |
| CROP | Crop resource: field, furrows, wheat, haystack |
| ORE | Ore resource: rocks, veins, mine cart, pickaxe |
| PUMP | Oil on land: pumpjack (the `beam` piece rocks in game) |
| RIG | Oil at sea: offshore rig with derrick and helipad |
| DROP | Supply drop: crate with parachute |
| PLAZA, HALL, HQ | City square, town hall (level 1 centre), capital headquarters |
| HOUSE, HOUSE2, FLATS, TOWER | Buildings added as a city levels up (one per level) |
| WALLS | City walls reward |
| REEDS, LILY | Shoreline decoration on lakes |
| PALM, PALM2, CACTUS | Desert and Tropical theme scenery |
| SNOWPINE, SNOWFIR, DRIFT | Winter theme scenery |
| DEAD, DEAD2 | Ashlands theme: charred trees with embers |
| POLE | City flagpole with a gold finial (the waving cloth is drawn in game) |

The `team` colour on roofs, trim and wall towers is swapped in game for the owner's colour (warm grey while neutral).
Inland water is not a Blender model: it's a rippling surface built in game (shader waves, teal shallows, shore foam).

Rebuild:
```
python env.py            # writes env.json
python env.py render     # also renders env_lineup and saves env.blend
python integrate_env.py ../../gridline-command.html
```

![lineup](env_lineup.webp)
