# Dungeoneer Feature Backlog

## Combat
- [ ] Initiative system (currently player goes first by default)
- [ ] Ranged combat
- [ ] Throwing entities as items (requires high level/STR check)
- [ ] Different weapons with different reach parameters
- [ ] Different combat skills like archery and unarmed combat
- [ ] Different movement per character
- [ ] Different room sizes 
- [ ] Move function like move, attack, etc. to entities.py
- [ ] Loot enemy corpse after killing them (enemy inventory remains, player can loot)
- [ ] Corpse object replacing dead enemy in room contents
- [ ] Different enemy tables with different attributes
- [ ] More implementation of LUCK attribute
- [ ] Fumble effect 3: weapon drop — lands at random adjacent tile, player must loot it back
- [ ] Enemy naming system — Goblin 1, Goblin 2 etc. when multiple of same type in room

## Items
- [ ] Consumable breaks when attacked
- [ ] Item pickup for entities (low-level enemies grabbed by strong player)

## Progression
- [ ] Character upgrade screen (main menu)
- [ ] Leveling system

## World
- [ ] Procedural dungeon generation
- [ ] Options menu
- [ ] Tables of enemies and item for random spawning

Note — all goblins share one animation timer. That's fine for now — they all animate in sync, which looks intentional rather than broken. Individual enemy animation timers would require storing them per entity, which is a bigger refactor. Add to backlog.




https://itch.io/game-assets/tag-knight
source for free assets to use

https://adrverissimo.itch.io/knight-pixel-art
Knight sprite link

https://lionheart963.itch.io/goblin-sprite 
Goblin sprite link