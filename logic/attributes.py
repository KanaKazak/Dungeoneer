class Attributes:
    """
    Stores character attributes and handles soft-capped scaling.
    """

    # =========================================================
    # INITIALIZATION
    # =========================================================

    def __init__(self, STR=0, CON=0, DEX=0, AGI=0, INT=0, WIS=0, CHA=0, LUCK=0):
        self.STR = STR
        self.CON = CON
        self.DEX = DEX
        self.AGI = AGI
        self.INT = INT
        self.WIS = WIS
        self.CHA = CHA
        self.LUCK = LUCK


    # =========================================================
    # SOFT CAP SYSTEM
    # =========================================================

    def apply_soft_cap(self, value, bonus):
        """
        Applies diminishing returns to a bonus based on attribute value.
        NOTE: Currently unused in get_attribute_bonus, but kept for flexibility.
        """
        if value <= 30:
            return bonus
        elif value <= 60:
            return bonus * 0.5
        elif value <= 80:
            return bonus * 0.25
        else:
            return bonus * 0.1


    def _soft_cap_value(self, value):
        """
        Core soft-cap scaling logic.
        Used internally by get_attribute_bonus.
        """
        if value <= 30:
            return value
        elif value <= 60:
            return 30 + (value - 30) * 0.5
        elif value <= 80:
            return 30 + 15 + (value - 60) * 0.25
        else:
            return 30 + 15 + 5 + (value - 80) * 0.1


    # =========================================================
    # ATTRIBUTE CALCULATION
    # =========================================================

    def get_attribute_bonus(self, attr_name):
        """
        Returns the effective value of an attribute after soft caps.
        """
        value = getattr(self, attr_name)
        return self._soft_cap_value(value)


    # =========================================================
    # DEBUG / DISPLAY
    # =========================================================

    def __repr__(self):
        """
        String representation for debugging and logging.
        """
        return (
            f"STR: {self.STR}  CON: {self.CON}  DEX: {self.DEX}  AGI: {self.AGI}\n"
            f"INT: {self.INT}  WIS: {self.WIS}  CHA: {self.CHA}  LUCK: {self.LUCK}"
        )