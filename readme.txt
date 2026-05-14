# Dungeoneer

A CLI-based roguelike RPG with turn-based, grid-based combat. Procedurally generated dungeons, persistent character progression, and a detailed combat system with attributes, critical hits, fumbles, and enemy AI.

> Pygame graphical frontend in active development.

---

## Core Loop

1. Launch game → main menu
2. New run starts → procedural dungeon generated (3–5 rooms)
3. Navigate rooms, fight enemies, loot items
4. Run ends on **death** or **victory** (collect the Gold Medal in the final room)
5. XP, level, and attributes persist to `saves/player_progress.json`

Mid-run state is not saved — roguelike design.

---

## Features

### Combat System
- **Action Point economy** — 4 AP per turn; every action has a cost
- **Attack rolls** — `d100 + attack_bonus + proficiency >= target AC`
- **Weapon tags** — Heavy (STR), Light (DEX), Versatile (higher of STR/DEX)
- **Critical hits** — expanded crit range based on LUCK attribute
- **Fumble table** — 6 bad outcomes including tripping, hitting yourself, dropping your weapon, giving the enemy a free attack
- **Melee range** — must be within 1 tile on both axes (diagonals included)

### Attributes
Eight attributes (0–100) with **soft caps** that reduce returns past thresholds:

| Attribute | Effect |
|---|---|
| STR | Heavy/versatile attack and damage bonus |
| DEX | Light/versatile attack and damage bonus |
| AGI | Evasion (AC), movement tiles per AP |
| CON | Max HP |
| INT | XP multiplier |
| WIS | Debuff resistance *(planned)* |
| CHA | NPC interactions *(planned)* |
| LUCK | Crit range, fumble saves, drop rates *(planned)* |

5 attribute points distributed freely on level up.

### Dungeon Generation
- 3–5 rooms per run, connected linearly
- Each room: 50% chance to spawn a goblin, 50% chance to spawn an item
- Final room always contains the Gold Medal (win condition)

### Progression
- XP per kill scales with enemy level and your INT multiplier
- Level threshold: `level × 100` XP
- Enemy stats also level up between runs (weighted by enemy type)

---

## Tech Stack

- **Language:** Python 3.12+
- **UI:** Pygame (in development)
- **Save format:** JSON
- **Planned:** Flask API for run history and leaderboard

---

## Project Structure

```
├── app.py                      # Entry point
├── ui/
│   └── renderer.py             # Pygame frontend (run this to play)
├── logic/
│   ├── game.py                 # Core game logic
│   ├── gamestate.py            # State management
│   ├── combat.py               # Attack rolls, damage, crits, fumbles
│   ├── enemy_ai.py             # Enemy behavior (move → attack)
│   ├── entities.py             # Player and enemy definitions
│   ├── attributes.py           # Stat calculations and soft caps
│   ├── dungeon.py              # Procedural dungeon generation
│   ├── movement.py             # Grid movement, AP cost, wall collision
│   ├── items.py                # Weapons and consumables
│   ├── loot.py                 # Drop tables
│   ├── inventory_manipulation.py
│   ├── input_handler.py
│   └── progress.py             # Save/load
├── saves/
│   └── player_progress.json
└── assets/                     # Sprites and animations
```

---

## Getting Started

### Prerequisites

- Python 3.12+
- pip

### 1. Clone the repo

```bash
git clone https://github.com/KanaKazak/dungeoneer.git
cd dungeoneer
```

### 2. Install dependencies

```bash
pip install pygame
```

### 3. Run the game

```bash
python ui/renderer.py
```

---

## Current Character: Knight

| STR | DEX | AGI | CON | INT | WIS | CHA | LUCK |
|---|---|---|---|---|---|---|---|
| 20 | 5 | 3 | 15 | 2 | 3 | 5 | 2 |

High damage, tanky, slow. More character templates planned.

---

## Backlog Highlights

- Fumble table, dodge action, ranged combat, status effects
- Armor system (AGI penalty vs. damage reduction tradeoff)
- Weapon enchantments and item rarity
- Expanded enemy roster with elite variants
- Branching dungeon generation, trap rooms, NPC merchants
- Flask API for run history and leaderboard
- Full Pygame graphical frontend

See [BACKLOG.md](BACKLOG.md) and [DESIGN.md](DESIGN.md) for the full picture.