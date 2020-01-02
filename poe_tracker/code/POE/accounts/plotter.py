import asyncio
import datetime as dt
import discord
import humanize
import io
import matplotlib
import numpy as np
import time

from ...Log import Log
from ...args import Args
from .. import mongo


class Plotter:
    log = Log()

    def __init__(self):
        # self.poe_sql = POE_SQL()
        self.db = mongo.Mongo().db
        self.args = Args()


    async def plot_character(self, characters, channel):
        # Not the best form, but matplotlib likes to fill our tests full of errors if we 
        # import this on module import...
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        class CustomYFormatter(matplotlib.ticker.Formatter):
            def __call__(self, x, pos=None):
                return humanize.intword(x, "%.3f")

            def format_data(self, value):
                return humanize.intword(value, "%.3f")

        self.log.info(characters)
        self.log.info(self.args)
        plot_sets = []
        characters_plotted = []
        for character in characters:
            x = []
            y = []
            async for xp in self.poe_sql.iter_character_xp(character):

                # Filter out items if we only want recent data
                if self.args.recent:
                    if (time.time() - xp['timestamp'])/60/60 > int(self.args.recent):
                        continue

                x.append(xp['timestamp'])
                y.append(xp['experience'])


            if self.args.differential:
                # Step through each point in y, and caluclate it's difference
                # Note that we drop a point along the way!
                y = np.asarray(y)
                # x = np.asarray(x)
                y = list(60*60*np.diff(y)/np.diff(np.asarray(x)))
                # We need to trim off the first element of x to makeup for the lost data in the differential
                x = x[1:]

            x = [dt.datetime.fromtimestamp(ts) for ts in x]

            if len(x):
                plot_sets.append((x,y,character.name))
                characters_plotted.append(character.name)
            else:
                self.log.warning(f"Fully filtered out {character.name}")

        if len(plot_sets) == 0:
            return

        plt.figure(figsize=(9,6))
        for plot_set in plot_sets:
            plt.plot(plot_set[0], plot_set[1], label=plot_set[2])

        ax = plt.gca()

        plt.legend()

        ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter('%Y-%m-%d %H:%M:%S'))
        plt.xticks( rotation=25 )

        # ax.yaxis.set_major_formatter(matplotlib.ticker.StrMethodFormatter('{humanize.intword(x)}'))
        ax.yaxis.set_major_formatter(CustomYFormatter())
        ax.set_ylabel('XP')

        #plt.subplots_adjust(bottom=0.2, left=0.2)

        plt.grid()

        # Save figure to ram for printing to discord
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight',dpi=100)
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
