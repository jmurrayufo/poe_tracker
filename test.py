#!/usr/bin/env python3.7

from pprint import pprint
import datetime
import json
import os
import time

from poe_tracker.code.Log import Log
from poe_tracker.code.POE.trade.api import TradeAPI
from poe_tracker.code.POE.trade import ChangeID

y = ChangeID("549996875-567500728-536738446-612155594-581566365")
x = ChangeID()
x.sync_poe_ninja()
print(x)
print(x-y)
