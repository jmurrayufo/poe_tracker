
import re

from ...Log import Log

class Price:
    """
    Given a note, return an estimated price of an item in terms of chaos orbs
    """

    price_re = re.compile(r"~(b\/o|price) *([\d\.\/]+) *([\w\- ']+)")
    valid_currencies = [
        "alch",
        "alt",
        "blessed",
        "cartographer",
        "chance",
        "chaos",
        "chisel",
        "chrom",
        "divine",
        "exa",
        "exalted" ,
        "fuse",
        "fusing",
        "gcp",
        "gemcutter",
        "jewel",
        "mir",
        "mirror",
        "perandus",
        "regal",
        "regret",
        "scour",
        "silver",
    ]

    currency_remapping = {
        "gcp":"gemcutter",
        "cartographer":"chisel",
        "fuse":"fusing",
        "exalted":"exa",
        "mirror":"mir",
    }

    item_remapping = {
        "alch":"Orb of Alchemy",
        "alt":"Orb of Alteration",
        "blessed":"Blessed Orb",
        "cartographer":"Cartographer's Chisel",
        "chance":"Orb of Chance",
        "chaos":"Chaos Orb",
        "chisel":"Cartographer's Chisel",
        "chrom":"Chromatic Orb",
        "divine":"Divine Orb",
        "exa":"Exalted Orb",
        "exalted" :"Exalted Orb",
        "fuse":"Orb of Fusing",
        "fusing":"Orb of Fusing",
        "gcp":"Gemcutter's Prism",
        "gemcutter":"Gemcutter's Prism",
        "jewel":"Jeweller's Orb",
        "mir":"Mirror of Kalandra",
        "mirror":"Mirror of Kalandra",
        "perandus":"Perandus Coin",
        "regal":"Regal Orb",
        "regret":"Orb of Regret",
        "scour":"Orb of Scouring",
        "silver":"Silver Coin",
    }


    def __init__(self, note=None, stack_size = 1):
        self.note = note
        self.value = 0
        self.value_name = "UNKNOWN"
        self.stack_size = stack_size
        self.log = Log()

    def __str__(self):
        return f"P(v={self.value}, n={self.value_name})"

    @property
    def cost(self):
        """
        Search current DB for estimations of how expensive this item is
        """

    def parse(self):
        """Check to see if we have a valid selling note, and save that data.
        Returns:
            True on sucessful parsing
            False on unparasble or missing note field
        """
        # Parse out the notes field if we can
        match_obj = self.price_re.search(self.note)
        if not match_obj:
            return False

        try:
            self.value = eval(match_obj.group(2)) if match_obj.group(2) is not None else 1
            # Prevent > 64 bit numbers from being parsed if someone gives us a really stupid field
            if self.value > 2**63:
                self.log.error(f"Saw value of {self.value} and corrected it to {2**63}. Note was {note}")
                self.value = 2**63
        except (SyntaxError, ZeroDivisionError):
            return False
        except TypeError:
            self.log.exception("Exception in parsing price value")
            self.log.error(f"Value was {self.value}")
            self.log.error(f"Stack Size {self.stack_size}")
            return False

        if type(self.value) not in [float,int]:
            self.value = 0
            self.value_name = "UNKNOWN"
            return False

        self.value_name = match_obj.group(3)
        
        if self.value_name not in self.valid_currencies:
            return False
        
        if self.value_name in self.currency_remapping:
            self.value_name = self.currency_remapping[self.value_name]

        if self.value_name in self.item_remapping:
            self.value_name = self.item_remapping[self.value_name]

        return True

class Estimate:

    def __init__(self, m=2):
        self.m=m

