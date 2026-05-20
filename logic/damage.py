# =========================================================
#DAMAGE TYPES
# =========================================================
class DamageType:
    """
    Enum-like class for damage types.
    """
    def __init__(self, slashing=0, bludgeoning=0, piercing=0, fire=0, cold=0, lightning=0, force=0, radiant=0, poison=0, necrotic=0, psychic=0, acid=0, sonic=0):
        self.slashing = slashing
        self.bludgeoning = bludgeoning
        self.piercing = piercing
        self.fire = fire
        self.cold = cold
        self.lightning = lightning
        self.force = force
        self.radiant = radiant
        self.poison = poison
        self.necrotic = necrotic
        self.psychic = psychic
        self.acid = acid
        self.sonic = sonic
    def as_dict(self):
        return {
            "slashing": self.slashing,
            "bludgeoning": self.bludgeoning,
            "piercing": self.piercing,
            "fire": self.fire,
            "cold": self.cold,
            "lightning": self.lightning,
            "force": self.force,
            "radiant": self.radiant,
            "poison": self.poison,
            "necrotic": self.necrotic,
            "psychic": self.psychic,
            "acid": self.acid,
            "sonic": self.sonic
        }
    def total(self):
        return sum(self.as_dict().values())

