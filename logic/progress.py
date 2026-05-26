import json

from logic.attributes import Attributes

def load_progress():
    path = "saves/player_progress.json"
    try:
        with open(path, 'r') as f:
            data = json.load(f)
            attributes = Attributes(**data.get("attributes", {
                "STR": 20, "CON": 15, "DEX": 5, "AGI": 3,
                "INT": 2, "WIS": 3, "CHA": 5, "LUCK": 2
            }))
            perks = data.get("perks", [])
            return data["exp"], data["level"], attributes, set(perks)
    except FileNotFoundError:
        return 0, 1, Attributes(STR=20, CON=15, DEX=5, AGI=3, INT=2, WIS=3, CHA=5, LUCK=2), set()

def save_progress(exp, level, attributes, perks):
    path = "saves/player_progress.json"
    data = {"exp": exp,
            "level": level,
            "attributes": {
                "STR": attributes.STR,
                "CON": attributes.CON,
                "DEX": attributes.DEX,
                "AGI": attributes.AGI,
                "INT": attributes.INT,
                "WIS": attributes.WIS,
                "CHA": attributes.CHA,
                "LUCK": attributes.LUCK
        },
        "perks": list(perks)
    }
    with open(path, 'w') as f:
        json.dump(data, f)