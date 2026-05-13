# Dungeoneer — Design Document
*Last updated: work in progress*

---

## Overview
Dungeoneer is a CLI-based roguelike RPG with turn-based, grid-based combat. Runs are procedurally generated and non-persistent — you cannot save mid-run. Progression (XP, level, attributes) persists between runs.

---

## Core Loop
1. Player launches game → main menu
2. New run starts → procedural dungeon generated
3. Player navigates rooms, fights enemies, loots items
4. Run ends on death or winning condition (collecting the Gold Medal)
5. XP, level, and attributes saved to `saves/player_progress.json`

---

## Turn System
Turns are **time-sensitive** only when enemies are present in the room.

### Action Points (AP)
- Every character has **4 AP per turn** (base)
- Outside combat: AP is not tracked, actions are free
- Inside combat: every action costs AP

| Action | AP Cost |
|---|---|
| Move (1 AP = movement_per_ap tiles) | 1 |
| Look | 1 |
| Attack (unarmed) | 1 |
| Attack (light weapon) | 1 |
| Attack (heavy/versatile weapon) | 2 |
| Loot | 1 |
| Inventory (open + use item) | 1 + 1 |
| Traverse (move to next room) | 4 |
| Dodge | 2 (to be implemented) |
| Position check (pos/where) | 0 (always free) |

---

## Movement
- Rooms are **10x10 grids**
- Player spawns at **(5, 1)** on entering a room
- Enemies spawn at random positions
- **1 AP = `movement_per_ap` tiles**, distributed freely across x/y axes (Manhattan distance)
- `movement_per_ap = 4 + AGI_bonus // 5`
- Hitting a wall moves you to the boundary and costs 1 extra movement as penalty
- Two entities cannot occupy the same tile

---

## Combat

### Attack Roll
```
roll (1-100) + attack_bonus + prof_bonus >= AC
```
- `attack_bonus` = `get_attribute_bonus(STR or DEX)` based on weapon tag
- `prof_bonus` = `level * 2`
- `AC` = `50 + get_attribute_bonus(AGI)` of defender

### Weapon Tags
| Tag | Attribute Used |
|---|---|
| Heavy | STR |
| Light | DEX |
| Versatile | Higher of STR or DEX |
| Unarmed | Higher of STR or DEX |

### Damage Roll
```
damage = weapon_damage + attack_bonus / 10 + prof_bonus
```
- Stored as float, displayed as float
- Enchantment bonus: to be implemented

### Critical Hit
- Roll >= `crit_threshold` → damage doubled
- `crit_threshold = 100 - LUCK_bonus // 5`
- Base: crit on 100 only. High LUCK extends range (e.g. LUCK 50 → crit on 95-100)

### Critical Miss (Fumble)
- Roll <= `fumble_threshold` → random bad effect
- `fumble_threshold = max(1, 2 - LUCK_bonus // 30)`
- LUCK save: on fumble, roll again — high LUCK gives small chance to downgrade to normal miss

#### Fumble Table
| # | Effect |
|---|---|
| 1 | Trip — lose all remaining AP |
| 2 | Hit yourself — take half your own damage |
| 3 | Drop weapon — lands at random adjacent tile |
| 4 | Stumble — enemy gets a free attack |
| 5 | Pull a muscle — movement_per_ap halved next turn |
| 6 | Embarrassing miss — enemy gets +10 to next attack roll |

### Melee Range
- Attacker and target must be within **1 tile** on both x and y axes (includes diagonals)
- `abs(ax - tx) <= 1 and abs(ay - ty) <= 1`

---

## Attributes
Range: **0–100**. Starting values depend on character template. 
Players gain **5 attribute points per level up** to distribute freely.

### Soft Caps
| Range | Effectiveness |
|---|---|
| 0–30 | 100% (full returns) |
| 31–60 | 50% |
| 61–80 | 25% |
| 81–100 | 10% (minimal returns) |

Players are warned when investing past a soft cap threshold.

### Attribute Effects

| Attribute | Effect |
|---|---|
| **STR** | Heavy/versatile attack roll bonus, damage bonus |
| **DEX** | Light/versatile attack roll bonus, damage bonus |
| **AGI** | AC (evasion), movement tiles per AP |
| **CON** | Max HP: `base_hp + CON_bonus * 2` |
| **INT** | EXP multiplier: `1 + INT_bonus * 0.005` |
| **WIS** | Debuff resistance (to be implemented) |
| **CHA** | Social interactions, NPC reactions (to be implemented) |
| **LUCK** | Crit range, fumble save chance, (future: drop rates, status chance, random EXP) |

---

## Character Templates

### Knight (current hardcoded character)
| STR | DEX | AGI | CON | INT | WIS | CHA | LUCK |
|---|---|---|---|---|---|---|---|
| 20 | 5 | 3 | 15 | 2 | 3 | 5 | 2 |

- Base HP: 100
- Playstyle: high damage, tanky, slow

---

## Progression
- XP gained per kill: `target.level * 10 * INT_multiplier`
- Level up threshold: `level * 100` XP
- Level up grants 5 attribute points
- Enemy level ups: weighted random attribute increase based on enemy type

### Goblin Level Up Weights
| Attribute | Weight |
|---|---|
| STR | 3 |
| DEX | 3 |
| CON | 2 |
| LUCK | 2 |
| AGI | 1 |

---

## Items

### Weapons
| Name | Damage | AP Cost | Tag |
|---|---|---|---|
| Rusty Sword | 5 | 2 | Versatile |
| Club | 4 | 1 | Heavy |

### Consumables
| Name | Effect |
|---|---|
| Health Potion | Restores 20 HP |

### Valuables
| Name | Value | Effect |
|---|---|---|
| Gold Medal | 100 | Win condition |

---

## Enemies

### Goblin
- Base HP: 30
- Damage: base_damage (unarmed)
- Starting attributes: STR 5, CON 5, DEX 3, AGI 3, INT 1, WIS 1, CHA 1, LUCK 2
- Equipped: Club
- AI: move toward player if out of range, attack if adjacent
- Drop: equipped weapon (lootable from corpse)

---

## Dungeon Generation
- **3–5 rooms** per run, connected linearly north→south
- Each room: 50% chance to spawn a goblin, 50% chance to spawn an item
- Last room always contains the Gold Medal (win condition)
- Room names and descriptions drawn from a table

### Room Table
| Name | Description |
|---|---|
| Damp Cellar | Moss covers the walls. |
| Bone Chamber | Bones litter the floor. |
| Forgotten Hall | A sense of dread fills the air. |
| Rat's Nest | The sound of dripping water echoes. |
| Dark Corridor | Shadows dance on the walls. |

---

## Save System
- File: `saves/player_progress.json`
- Saved on: death, victory, quit game
- Contents: XP, level, all attributes
- Mid-run state is NOT saved (roguelike design)

---

## Backlog (To Be Implemented)
### Combat
- [ ] Fumble table implementation
- [ ] Crit and fumble with LUCK save
- [ ] Dodge action (2 AP, reduces hit chance)
- [ ] Ranged combat
- [ ] Status effects / debuffs
- [ ] Throwing entities as items (high STR check)
- [ ] Consumable breaks when attacked

### Attributes
- [ ] WIS: debuff resistance
- [ ] CHA: NPC interactions, shop prices
- [ ] LUCK: random EXP bonus, status effect chance, drop rates

### Items & Equipment
- [ ] Weapon enchantments
- [ ] Armor (AGI penalty / damage reduction tradeoff)
- [ ] Item rarity system
- [ ] Enemy-specific item tables / loot pools

### Enemies
- [ ] Enemy roster with different attribute spreads
- [ ] Elite/champion variants
- [ ] Enemy skill system (unarmed combat skills)

### Progression
- [ ] Unarmed combat skill tree
- [ ] Skill learning speed affected by INT
- [ ] Character roster (multiple starting templates)
- [ ] Upgrade character menu (between runs)

### World
- [ ] Branching dungeon generation (non-linear)
- [ ] Trap rooms, puzzle rooms
- [ ] NPC merchants

### Technical
- [ ] Flask API (run history, stats, leaderboard)
- [ ] Graphical frontend (Pygame or browser-based)
- [ ] Melee range validation polish
- [ ] Refactor: action methods on Character class
- [ ] Proficiency bonus soft cap or logarithmic scaling (currently level * 2 dominates late game)
