# Gridline Command

A turn-based tactics game in your browser: capture every enemy HQ. Low-poly 3D, four factions, a 22-tech research tree, solo games against the AI and live online matches for up to four players.

**Play:** https://kyleberger98.github.io/Operation-Foothold/

The whole game is one file, `gridline-command.html`. It also runs offline: download it and open it in any modern browser.

## What's in it

- **Seven factions**, each with its own perk and a once-per-game commander power.
- **Two modes:** Conquest (capture every HQ) and Score attack (30 turns, highest score wins).
- **Stars and medals:** every solo win is rated one to three stars, and each faction keeps its best medal per difficulty.
- **Pass & play:** two to four people can share one phone or computer, each with their own fog of war.
- **Online:** live matches for up to four players with an invite link.

## Install it on your phone

Gridline Command installs like an app, with its own home-screen icon, full-screen play and offline single-player:

- **Android (Chrome):** open the game and tap **Install app** on the title screen (or Chrome's menu → *Install app*).
- **iPhone / iPad (Safari):** open the game, tap **Share**, then **Add to Home Screen**.

Once installed it opens straight into the game and works without a connection (online matches still need the internet). Updates arrive automatically the next time you open it online.

## Playing with friends

1. On the title screen tap **Online**, then **Host Operation**.
2. Tap **Copy invite link** (or **Share invite** on a phone) and send it to up to three friends.
3. The link opens the game with your room code filled in. They tap **Join**, you tap **Launch Operation**.

Everyone plays live, and the host's device runs the match, so the host keeps the game open until the end. Friends can also join by typing the 5-letter room code under Online → Join.

## Repository

| Path | What it is |
|---|---|
| `gridline-command.html` | The game |
| `operation-foothold-final.html` | The old file name (the game used to be called Operation Foothold); forwards to the game so old links keep working |
| `index.html` | Forwards the short address (and invite links) to the game |
| `manifest.webmanifest`, `sw.js`, `icons/` | Make the game installable on phones and playable offline |
| `art/units/` | Blender source for the unit models; see its README |
