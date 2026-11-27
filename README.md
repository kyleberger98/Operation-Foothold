# Gridline Command

A turn-based tactics game for the browser where you capture every enemy HQ. Low-poly 3D, seven factions, a 24-tech research tree, solo games against the AI and live online matches for up to four players.

**Play:** https://kyleberger98.github.io/Operation-Foothold/

The whole game is one file, `gridline-command.html`. It also runs offline if you download it and open it in any modern browser.

## What's in it

- **Seven factions**, each with its own perk and a once-per-game commander power.
- **Titans** are super units that only cities of level 4 or higher can field, one per city. Each blow also hits the enemies next to the target, and a level-5 city can become a Titan foundry that trains them cheaper.
- Coastal cities build a **navy** of Patrol Boats, Landing Craft, Destroyers and Battleships. Landing Craft ferry land units across water.
- Seven **map types** (Classic, Highlands with mountain ridges and passes, Woodland with forest groves, River, Lakes, Inland Sea and Mirrored) and eight optional **modifiers** (No fog, Double income, Early Titans, No powers, Scarce stars, Fortress world, Barren land and Turn limit, which ends the game on score after 40 turns). Players start in a random corner, and skirmish maps are chosen so villages and resources split evenly between HQs.
- Contested **airdrops** land near the middle of the map from turn 10.
- A **campaign** where you conquer a random map of regions one battle at a time against three rival factions. Battles have their own objectives (conquest, raids, holding out, two-front fights and capital assaults), and a capital can only be attacked once you hold two regions next to it and it holds none of them.
- **Buildings** on your own territory grow your economy. Farms, Lumber Camps and Quarries grow cities, and Ports, Factories and Markets pay stars every turn (Factories and Markets get more from neighbouring buildings).
- **Diplomacy** with every faction covers war, 10-turn peace treaties and alliances (shared sight, shared victory), plus star gifts and tribute. Computer rivals weigh offers by strength, threats and trust. A much stronger computer rival may mass troops on your border and then break a peace, and computer allies may leave an alliance. A shared victory counts as a full win only if you hold a third of the allies' cities or score. Online, other players answer your proposals.
- Every finished game earns XP toward 30 **Commander ranks**, which unlock board themes (Autumn, Desert, Winter, Tropical, Dusk, Ashlands), unit finishes and city flag emblems. They change looks only, never gameplay.
- **Two modes:** Conquest (capture every HQ) and Score attack (30 turns, highest score wins). Stalled conquest games end on score after a 10-turn warning.
- Five **difficulty levels** (Easy, Normal, Hard, Brutal, Crazy). Computer rivals play under the same fog of war as you.
- Every solo win is rated one to three **stars**, and each faction keeps its best **medal** per difficulty.
- **Pass & play** lets two to four people share one phone or computer, each with their own fog of war.
- Live **online** matches for up to four players, joined with an invite link. Dropped players keep their seat (the AI fills in until they rejoin), the host can resume a room after a reload, and players can send quick preset messages. Each player's rank and flag show in the lobby.
- A **guided first game:** your first Quick play is a short tutorial on a small map against one easy rival, and the first few games point out buildings, diplomacy and your commander power. The Field Manual (the ? button) is split into sections.
- **Settings** on the title screen for sound, music and effects levels, graphics (High or Low), camera follow and text size, kept on each device. Esc closes the open panel, and a missile strike always takes a confirm tap or click.
- **Accessibility:** a Text size setting (Normal, Large, Larger), faction symbols on unit and city labels so sides don't rely on colour alone, and support for the system reduce-motion setting (no camera follow, no pulsing).

## Install it on your phone

Gridline Command installs like an app, with its own home-screen icon, full-screen play and offline single-player:

- **Android (Chrome):** open the game and tap **Install app** on the title screen (or *Install app* in Chrome's menu).
- **iPhone / iPad (Safari):** open the game, tap **Share**, then **Add to Home Screen**.

Once installed it opens straight into the game and works without a connection (online matches still need the internet). Updates arrive automatically the next time you open it online. On a slow connection the installed game opens from its saved copy after 3 seconds and picks up the update the next time.

Phones with 2 GB of memory or less, or that draw the first game slowly, start on Low graphics (fewer trees, no shadows, 30 fps). Change it in the menu. If the browser limits the game to 30 fps (for example in low power mode), the game does not decide and checks again the next time it opens.

## Playing with friends

1. On the title screen tap **Online**, then **Host Operation**.
2. Tap **Copy invite link** (or **Share invite** on a phone) and send it to up to three friends.
3. The link opens the game with your room code filled in. They tap **Join**, you tap **Launch Operation**.

Everyone plays live, and the host's device runs the match, so the host keeps the game open until the end. Friends can also join by typing the 5-letter room code on the **Online** screen and tapping **Join**. If the host's game closes, the host taps **Resume room** on the title screen and guests reconnect on their own.

## Repository

| Path | What it is |
|---|---|
| `gridline-command.html` | The game |
| `operation-foothold-final.html` | The old file name (the game used to be called Operation Foothold); forwards to the game so old links keep working |
| `index.html` | Forwards the short address (and invite links) to the game |
| `manifest.webmanifest`, `sw.js`, `icons/` | Make the game installable on phones and playable offline. Bump `VERSION` in `sw.js` with each release so the icons and manifest refresh |
| `art/units/`, `art/env/` | Blender sources for the unit models and the terrain, resource and building models; see their READMEs |
