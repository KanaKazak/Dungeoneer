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
            return data["exp"], data["level"], attributes
    except FileNotFoundError:
        return 0, 1, Attributes(STR=20, CON=15, DEX=5, AGI=3, INT=2, WIS=3, CHA=5, LUCK=2)

def save_progress(exp, level, attributes):
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
        }
    }
    with open(path, 'w') as f:
        json.dump(data, f)