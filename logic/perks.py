PERKS = {
    "war_hardened": {
        "name": "War-Hardened",
        "attribute": "STR",
        "threshold": 10,
        "description": "+5 max HP per 10 STR",
        "branch": "Raw Power"
    },
    "scholar": {
        "name": "Scholar",
        "attribute": "INT",
        "threshold": 10,
        "description": "+20% XP from all sources",
        "branch": "Arcane Knowledge"
    },
    "thick_hide": {
        "name": "Thick Hide",
        "attribute": "CON",
        "threshold": 10,
        "description": "2 AC always",
        "branch": "Toughness"
    },
    "steady_aim": {
        "name": "Steady Aim",
        "attribute": "DEX",
        "threshold": 10,
        "description": "+10 attack bonus with ranged weapons",
        "branch": "Precision"
    }
}

def get_available_perks(player):
    available = []
    for perk_key, perk in PERKS.items():
        if getattr(player.attributes, perk["attribute"]) >= perk["threshold"] and perk_key not in player.perks:
            available.append((perk_key, perk))
    return available