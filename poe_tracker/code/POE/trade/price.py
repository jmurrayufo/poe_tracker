
import re

from ...Log import Log

class Price:
    """
    Given a note, return an estimated price of an item in terms of chaos orbs
    """

    price_re = re.compile(r"^~(b\/o|price) *([\d\.\/,]+)? *([\w\- ']+)$")
    valid_currencies = [
        "chrom",
        "alt",
        "jewel",
        "chance",
        "chisel",
        "cartographer",
        "fuse",
        "fusing",
        "alch",
        "scour",
        "blessed",
        "chaos",
        "regret",
        "regal",
        "gcp",
        "gemcutter",
        "divine",
        "exalted" ,
        "exa",
        "mirror",
        "perandus",
        "silver",
        "mirror",
        "mir",
    ]

    currency_remapping = {
        "gcp":"gemcutter",
        "cartographer":"chisel",
        "fuse":"fusing",
        "exalted":"exa",
        "mirror":"mir",
    }


    def __init__(self, note):
        self.note = note
        self.value = 0
        self.value_name = "UNKNOWN"
        self.log = Log()

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
        # self.log.info(f"Attemt to split {self.note}")
        match_obj = self.price_re.search(self.note)
        if not match_obj:
            # self.log.error("Parse failed")
            # with open("errors.txt","a") as fp:
            #     fp.write(f"{self.note}\n")
            return False

        try:
            self.value = eval(match_obj.group(2)) if match_obj.group(2) is not None else 1
        except (SyntaxError, ZeroDivisionError):
            # self.log.exception("Eval errored out, catch and return")
            return False

        if type(self.value) not in [float,int]:
            # with open("errors.txt","a") as fp:
            #     fp.write(f"{self.note}\n")
            # self.log.error("Failed to parse")
            self.value = 0
            self.value_name = "UNKNOWN"
            return False

        self.value_name = match_obj.group(3)
        
        if self.value_name not in self.valid_currencies:
            return False
        
        if self.value_name in self.currency_remapping:
            self.value_name = self.currency_remapping[self.value_name]

        return True

