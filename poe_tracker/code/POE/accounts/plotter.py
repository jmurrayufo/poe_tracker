import asyncio
import datetime
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
        self.db = mongo.Mongo().db
        self.args = Args()


    async def plot_character(self, args, characters):
        # Not the best form, but matplotlib likes to fill our tests full of errors if we 
        # import this on module import...
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        class CustomYFormatter(matplotlib.ticker.Formatter):
            def __call__(self, x, pos=None):
                return humanize.intword(x, "%.3f")

            def format_data(self, value):
                return humanize.intword(value, "%.3f")

        self.log.info("Begin to handle plotting")
        self.log.info(characters)
        self.log.info(args)
        plot_sets = []
        characters_plotted = []
        for character in characters:
            x = []
            y = []
            async for xp_dict in self.db.characters.xp.find({"name":character},sort=[("date":-1)]):
                # Filter out items if we only want recent data
                if args.recent:
                    if (datetime.datetime.utcnow() - xp_dict['date']).total_seconds()/60/60 > args.recent:
                        continue

                x.append(xp_dict['date'])
                y.append(xp_dict['experience'])

            if args.differential:
                # Step through each point in y, and caluclate it's difference
                # Note that we drop a point along the way!
                y = np.asarray(y)
                x = [i.timestamp() for i in x]
                # x = np.asarray(x)
                y = list(60*60*np.diff(y)/np.diff(np.asarray(x)))
                # We need to trim off the first element of x to makeup for the lost data in the differential
                x = x[1:]
                x = [datetime.datetime.utcfromtimestamp(i) for i in x]

            if len(x):
                plot_sets.append((x,y,character))
                characters_plotted.append(character)
            else:
                self.log.warning(f"Fully filtered out {character.name}")

        if len(plot_sets) == 0:
            return

        self.log.info("Init plots")
        plt.figure(figsize=(9,6))
        for plot_set in plot_sets:
            plt.plot(plot_set[0], plot_set[1], label=plot_set[2])

        self.log.info("Config plots")
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
        self.log.info("Write plots to buffer")
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight',dpi=100)
        buf.seek(0)
        f = discord.File(buf, filename="chart.png")

        # Send message to discord
        self.log.info("Send to discord")
        message = f"Plotting for characters: {', '.join(characters_plotted)}"
        await args.message.channel.send(message, file=f)
        self.log.info("Plot completed")



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
