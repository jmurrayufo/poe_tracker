from collections import defaultdict
from pprint import pprint
import math
import re
import requests
import sys
import time
import time

from ..Singleton import Singleton
from ..Log import Log

class TradeAPI(metaclass=Singleton):

    poe_trade_url = "http://www.pathofexile.com/api/public-stash-tabs"

    def __init__(self):

        self.log = Log()

        # Set to True when we sync with the current change_ids on the server
        self.synced = False
        # This is a 5 element list of the current change IDs
        self.change_ids = [1,1,1,1,1]
        self.data = {}
        self.data_size = 0
        self.last_data_pull = time.time()


    def pull_data(self):
        """
        Update data from the API.
        """
        # print(r.headers['X-Rate-Limit-Ip'])
        # print(r.headers['X-Rate-Limit-Ip-State'])
        # TODO: Consider checking this header and delaying after call?
        # if r.headers['X-Rate-Limit-Ip-State'][0] == '2':
        # time.sleep(max(0, 0.5 - (time.time() - self.last_data_pull )))
        r = requests.get(
            self.poe_trade_url,
            params={"id":self.gen_change_id()},
            )

        # print(r.headers['X-Rate-Limit-Ip'])
        # print(r.headers['X-Rate-Limit-Ip-State'])
        try:
            if r.headers['X-Rate-Limit-Ip-State'][0] != '1':
                # print(r.json())
                # print(r.text)
                # print(r.headers)
                # exit()
                time.sleep(0.5)
        except Exception as e:
            print(r)
            print(r.status_code)
            print(e)
            return
        self.last_data_pull = time.time()
        self.data = r.json()
        self.data_size = sys.getsizeof(r.text)


    def gen_change_id(self):
        return f"{'-'.join(str(x) for x in self.change_ids)}"


    def iter_data(self):
        while 1:
            self.pull_data()
            yield self.data
            self.set_next_change_id()


    def set_next_change_id(self):
        server_next_change_id = self.data['next_change_id']
        server_change_ids = re.match(r"(\d+)-(\d+)-(\d+)-(\d+)-(\d+)", server_next_change_id).groups()
        self.change_ids = [int(x) for x in server_change_ids] 


    def sync_change_ids(self):
        # TODO: Make this async when done

        # [low,high,search_stage,search active]
        # Search Stages:
        #   0: find upper bound, double max each bad guess.
        #   1: Binary isolation
        #   2: Target locked
        print("Lets guess")
        guesses = {}
        # Initial guesses are setup to be the current change IDs. This will allow rapid catchup!
        guesses[0] = [self.change_ids[0],self.change_ids[0],0,True]
        guesses[1] = [self.change_ids[1],self.change_ids[1],0,True]
        guesses[2] = [self.change_ids[2],self.change_ids[2],0,True]
        guesses[3] = [self.change_ids[3],self.change_ids[3],0,True]
        guesses[4] = [self.change_ids[4],self.change_ids[4],0,True]

        while 1:
            print()
            for key in guesses:
                if guesses[key][3]:
                    break
            else:
                print("All keys locked, break")
                break

            print("Still keys to find!")

            # Set current self.change_ids based on direction of guesses
            # Hit poe_trade_url
            # Update guesses based on their stage
            for key in guesses:
                if guesses[key][2] == 0:
                    guesses[key][1] *= 2
                    guesses[key][1] = int(guesses[key][1])
                    self.change_ids[key] = guesses[key][1]

                elif guesses[key][2] == 1:
                    pass
                    # self.change_ids[key] = int((guesses[key][0] + guesses[key][1])/2)

                elif guesses[key][2] == 2:
                    pass

            # pprint(guesses)
            for key in guesses:
                # print(f"[{key}] {math.log(guesses[key][1]-guesses[key][0],2):.3f} {guesses[key][2]} {guesses[key][3]}")
                print(f"[{key}] {guesses[key][1]-guesses[key][0]:,d} {guesses[key][2]} {guesses[key][3]}")

            self.pull_data()
            server_next_change_id = self.data['next_change_id']
            server_change_ids = re.match(r"(\d+)-(\d+)-(\d+)-(\d+)-(\d+)", server_next_change_id).groups()
            server_change_ids = [int(x) for x in server_change_ids]
            # print(server_change_ids)

            # Process results
            for key in guesses:
                if guesses[key][2] == 0:
                    if server_change_ids[key] == guesses[key][1]:
                        # Move guess to binary search
                        guesses[key][2] = 1
                        # guesses[key][3] = False
                    else:
                        # Speed up the guess process by jumping the ID to at least the next given by the server
                        guesses[key][1] = server_change_ids[key]

                elif guesses[key][2] == 1:
                    # Check if we were high
                    # print(f"Compare {server_change_ids[key]:,d} to {self.change_ids[key]:,d}")                 
                    if server_change_ids[key] == self.change_ids[key]:
                        guesses[key][1] = self.change_ids[key]
                        self.change_ids[key] = int(guesses[key][0]*.5 + guesses[key][1]*.5)

                    # Else we were low
                    else:
                        guesses[key][0] = max(server_change_ids[key], self.change_ids[key])
                        self.change_ids[key] = int(guesses[key][0]*.5 + guesses[key][1]*.5)


                    if guesses[key][1] - guesses[key][0] < 100:
                        self.change_ids[key] = guesses[key][0]
                        guesses[key][2] = 2
                        guesses[key][3] = False

                elif guesses[key][2] == 2:
                    pass
                    # We already locked our target

"""Notes:

    Check out https://poe.ninja/api/Data/GetStats, it gives us the current next ID!!

"""
