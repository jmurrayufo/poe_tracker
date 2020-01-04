

class XPMath:

    xp_table = [
        (1,   0,          525),
        (2,   525,        1235),
        (3,   1760,       2021),
        (4,   3781,       3403),
        (5,   7184,       5002),
        (6,   12186,      7138),
        (7,   19324,      10053),
        (8,   29377,      13804),
        (9,   43181,      18512),
        (10,  61693,      24297),
        (11,  85990,      31516),
        (12,  117506,     39878),
        (13,  157384,     50352),
        (14,  207736,     62261),
        (15,  269997,     76465),
        (16,  346462,     92806),
        (17,  439268,     112027),
        (18,  551295,     133876),
        (19,  685171,     158538),
        (20,  843709,     187025),
        (21,  1030734,    218895),
        (22,  1249629,    255366),
        (23,  1504995,    295852),
        (24,  1800847,    341805),
        (25,  2142652,    392470),
        (26,  2535122,    449555),
        (27,  2984677,    512121),
        (28,  3496798,    583857),
        (29,  4080655,    662181),
        (30,  4742836,    747411),
        (31,  5490247,    844146),
        (32,  6334393,    949053),
        (33,  7283446,    1064952),
        (34,  8384398,    1192712),
        (35,  9541110,    1333241),
        (36,  10874351,   1487491),
        (37,  12361842,   1656447),
        (38,  14018289,   1841143),
        (39,  15859432,   2046202),
        (40,  17905634,   2265837),
        (41,  20171471,   2508528),
        (42,  22679999,   2776124),
        (43,  25456123,   3061734),
        (44,  28517857,   3379914),
        (45,  31897771,   3723676),
        (46,  35621447,   4099570),
        (47,  39721017,   4504444),
        (48,  44225461,   4951099),
        (49,  49176560,   5430907),
        (50,  54607467,   5957868),
        (51,  60565335,   6528910),
        (52,  67094245,   7153414),
        (53,  74247659,   7827968),
        (54,  82075627,   8555414),
        (55,  90631041,   9353933),
        (56,  99984974,   10212541),
        (57,  110197515,  11142646),
        (58,  121340161,  12157041),
        (59,  133497202,  13252160),
        (60,  146749362,  14441758),
        (61,  161191120,  15731508),
        (62,  176922628,  17127265),
        (63,  194049893,  18635053),
        (64,  212684946,  20271765),
        (65,  232956711,  22044909),
        (66,  255001620,  23950783),
        (67,  278952403,  26019833),
        (68,  304972236,  28261412),
        (69,  333233648,  30672515),
        (70,  363906163,  33287878),
        (71,  397194041,  36118904),
        (72,  433312945,  39163425),
        (73,  472476370,  42460810),
        (74,  514937180,  46024718),
        (75,  560961898,  49853964),
        (76,  610815862,  54008554),
        (77,  664824416,  58473753),
        (78,  723298169,  63314495),
        (79,  786612664,  68516464),
        (80,  855129128,  74132190),
        (81,  929261318,  80182477),
        (82,  1009443795, 86725730),
        (83,  1096169525, 93748717),
        (84,  1189918242, 101352108),
        (85,  1291270350, 109524907),
        (86,  1400795257, 118335069),
        (87,  1519130326, 127813148),
        (88,  1646943474, 138033822),
        (89,  1784977296, 149032822),
        (90,  1934009687, 160890604),
        (91,  2094900291, 173648795),
        (92,  2268549086, 187372170),
        (93,  2455921256, 202153736),
        (94,  2658074992, 218041909),
        (95,  2876116901, 235163399),
        (96,  3111280300, 253547862),
        (97,  3364828162, 273358532),
        (98,  3638186694, 294631836),
        (99,  3932818530, 317515914),
        (100, 4250334444, 0),
    ]


    def __init__(self):
        pass


    def level(self, xp):
        for idx in range(100):
            if self.xp_table[99-idx][1] <= xp:
                return self.xp_table[99-idx][0]


    def get_level(self, level):
        """Given a specific level, return the XP total and XP level amount
        """
        level = int(level)
        if 1 > level > 100:
            raise ValueError("Level must be between 1 and 100, inclusive")
        
        for l in self.xp_table:
            if l[0] == level:
                return (l[1], l[2])


    def level_percent(self, xp):
        """Given a set amount of xp, return % of level acomplished
        """
        current_level = self.level(xp)
        if current_level == 100:
            return 1
        current_level_min_xp = self.get_level(current_level)[0]
        next_level_min_xp = self.get_level(current_level+1)[0]
        return (xp-current_level_min_xp)/(next_level_min_xp-current_level_min_xp)


    def total_percent(self, xp):
        """Total progress to level 100, expressed in [0.0, 1.0]
        """
        return xp/self.xp_table[-1][1]


    def xp_bar(self, xp, bubbles=20, start='[', end=']', fill='=', to_100=False):
        if to_100:
            percent = self.total_percent(xp)
        else:
            percent = self.level_percent(xp)
        ret_val = start
        fill_bubbles = bubbles * percent
        ret_val += fill * int(fill_bubbles)
        ret_val += " " * (bubbles - int(fill_bubbles))
        ret_val += end
        return ret_val
