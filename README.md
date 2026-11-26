# Gridline Command

A turn-based tactics game for the browser where you capture every enemy HQ. Low-poly 3D, seven factions, a 24-tech research tree, solo games against the AI and live online matches for up to four players.

**Play:** https://kyleberger98.github.io/Operation-Foothold/

The whole game is one file, `gridline-command.html`. It also runs offline if you download it and open it in any modern browser.

## What's in it

- **Seven factions**, each with its own perk and a once-per-game commander power.
- **Titans** are super units that only cities of level 4 or higher can field, one per city.
- Coastal cities build a **navy** of Patrol Boats, Landing Craft, Destroyers and Battleships. Landing Craft ferry land units across water.
- Six **map types** (Classic, Highlands, Woodland, Lakes, Inland Sea and Mirrored) and four optional **modifiers** (No fog, Double income, Early Titans and No powers).
- A **campaign** where you conquer a random map of regions one battle at a time against three rival factions. Each battle is a normal game.
- **Buildings** on your own territory grow your economy. Farms, Lumber Camps and Quarries grow cities, and Ports, Factories and Markets pay stars every turn (Factories and Markets get more from neighbouring buildings).
- **Diplomacy** with every faction covers war, 10-turn peace treaties and alliances (shared sight, shared victory), plus star gifts and tribute. Computer rivals weigh offers by strength, threats and trust. Online, other players answer your proposals.
- Every finished game earns XP toward 30 **Commander ranks**, which unlock board themes (Autumn, Desert, Winter, Tropical, Dusk, Ashlands), unit finishes and city flag emblems. They change looks only, never gameplay.
- **Two modes:** Conquest (capture every HQ) and Score attack (30 turns, highest score wins).
- Every solo win is rated one to three **stars**, and each faction keeps its best **medal** per difficulty.
- **Pass & play** lets two to four people share one phone or computer, each with their own fog of war.
- Live **online** matches for up to four players, joined with an invite link.

## Install it on your phone

Gridline Command installs like an app, with its own home-screen icon, full-screen play and offline single-player:

- **Android (Chrome):** open the game and tap **Install app** on the title screen (or *Install app* in Chrome's menu).
- **iPhone / iPad (Safari):** open the game, tap **Share**, then **Add to Home Screen**.

Once installed it opens straight into the game and works without a connection (online matches still need the internet). Updates arrive automatically the next time you open it online.

## Playing with friends

1. On the title screen tap **Online**, then **Host Operation**.
2. Tap **Copy invite link** (or **Share invite** on a phone) and send it to up to three friends.
3. The link opens the game with your room code filled in. They tap **Join**, you tap **Launch Operation**.

Everyone plays live, and the host's device runs the match, so the host keeps the game open until the end. Friends can also join by typing the 5-letter room code on the **Online** screen and tapping **Join**.

## Repository

| Path | What it is |
|---|---|
| `gridline-command.html` | The game |
| `operation-foothold-final.html` | The old file name (the game used to be called Operation Foothold); forwards to the game so old links keep working |
| `index.html` | Forwards the short address (and invite links) to the game |
| `manifest.webmanifest`, `sw.js`, `icons/` | Make the game installable on phones and playable offline |
| `art/units/`, `art/env/` | Blender sources for the unit models and the terrain, resource and building models; see their READMEs |
