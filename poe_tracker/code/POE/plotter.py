import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from ..Log import Log
import io
import discord
import datetime as dt

from . import POE_SQL

class Plotter:
    log = Log()

    def __init__(self):
        self.poe_sql = POE_SQL()
        pass


    async def plot_character(self, character, channel):
        x = []
        y = []
        async for xp in self.poe_sql.iter_character_xp(character):
            x.append(xp['timestamp'])
            y.append(xp['experience']/1e6)

        x = [dt.datetime.fromtimestamp(ts) for ts in x]
        plt.figure()
        plt.plot(x,y,'o')
        ax = plt.gca()

        plt.title(f"{character.name}")

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
        await channel.send(file=f)
    
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