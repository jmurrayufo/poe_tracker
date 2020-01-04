

from ...Log import Log

class ItemBase:
    """Base of all items
    """

    def __init__(self, item_dict=None):

        self.x = item_dict.get("x", None)
        self.y = item_dict.get("y", None)

        self.h = item_dict.get("h", None)
        self.w = item_dict.get("w", None)

        self.name = item_dict.get("name", None)
        self.type_line = item_dict.get("type_line", None)
        self.league = item_dict.get("league", None)
        self.frame_type = item_dict.get("frameType", None)

        self.note = item_dict.get("note", None)
        self._has_valid_note = False


    def parse_sellers_note(self):
        """Check to see if we have a valid selling note, and save that data.
        Returns:
            True on sucessful parsing
            False on unparasble or missing note field
        """
        if self._has_valid_note is True:
            return True
        if self.note is None:
            return False


        # if 'note' not in item:
        #     continue
        # if not item['note'].startswith("~"):
        #     continue
        # try:
        #     item['note'].encode().decode('ascii')
        # except UnicodeDecodeError:
        #     continue
        # if item['extended']['category'] != "currency":
        #     continue

        # Parse out the notes field if we can
        self.log.info(f"Attemt to split {item_dict['note']}")
        match_obj = re.search(r"~(b\/o|price) *([\d\.\/,]+)? *([\w\- ']+)$", item_dict['note'])
        if match_obj:
            self.log.info(match_obj.groups())
            pass
        else:
            self.log.error("Parse failed")
            with open("errors.txt","a") as fp:
                fp.write(f"{item_dict['note']}\n")
            return

        try:
            value = eval(match_obj.group(2)) if match_obj.group(2) is not None else 1
        except (SyntaxError, ZeroDivisionError):
            self.log.exception("Eval errored out, catch and return")
            return

        if type(value) not in [float,int]:
            with open("errors.txt","a") as fp:
                fp.write(f"{item_dict['note']}\n")
            self.log.error("Failed to parse")
            return

# We really should just move item base, but i'm lazy
from . import currency

class ItemGenerator:

    log = Log()

    def __new__(cls, item_dict):
        """
        Given an item dict from the POE Stash Tab API, return some sort of item class
        """

        if item_dict['extended']['category'] == "currency":
            return currency.Currency(item_dict)

        raise TypeError("No valid item type for this exists yet!")


