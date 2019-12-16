import datetime as dt
import discord
import io
import numpy as np
import time
import asyncio

from ..Log import Log
from . import POE_SQL

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


class Plotter:
    log = Log()

    def __init__(self, args):
        self.poe_sql = POE_SQL()
        self.args = args
        pass


    async def plot_character(self, characters, channel):

        self.log.info(characters)
        self.log.info(self.args)
        plot_sets = []
        characters_plotted = []
        for character in characters:
            x = []
            y = []
            async for xp in self.poe_sql.iter_character_xp(character):

                if self.args.recent:
                    if (time.time() - xp['timestamp'])/60/60 > int(self.args.recent):
                        continue

                x.append(xp['timestamp'])
                y.append(xp['experience']/1e6)

            x = [dt.datetime.fromtimestamp(ts) for ts in x]
            if len(x):
                plot_sets.append((x,y,character.name))
                characters_plotted.append(character.name)
            else:
                self.log.warning(f"Fully filtered out {character.name}")

        if len(plot_sets) == 0:
            return

        plt.figure()
        for plot_set in plot_sets:
            plt.plot(plot_set[0], plot_set[1], label=plot_set[2])

        ax = plt.gca()

        plt.legend()

        ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter('%Y-%m-%d %H:%M:%S'))
        plt.xticks( rotation=25 )

        ax.yaxis.set_major_formatter(matplotlib.ticker.StrMethodFormatter('{x:,.0f}'))
        ax.set_ylabel('XP (Millions)')

        plt.subplots_adjust(bottom=0.2)

        # Save figure to ram for printing to discord
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        f = discord.File(buf, filename="chart.png")

        # Send message to discord
        message = f"Plotting for characters: {', '.join(characters_plotted)}"
        await channel.send(message, file=f)
    
"""
import io
from PIL import Image
import matplotlib.pyplot as plt

plt.figure()
plt.plot([1, 2])
plt.title("test")
buf = io.BytesIO()
plt.savefig(buf, format='png')
buf.seek(0)
im = Image.open(buf)
im.show()
buf.close()
"""