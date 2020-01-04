
import datetime
import discord
import random

from . import xp_math

def ding_embed(character):
    """Given a mongodb character JSON, return a level up embed
    """
    fun_messages = (
        "Ding!",
        "Level up!",
        "Power up!",
        "Gratz!",
        "It's over 9000!!!",
        "Hey look, he figured out how to socket a gem!",
        )

    em = discord.Embed(
            color = discord.Color.gold(),
            title=character['name'],
            timestamp=datetime.datetime.now(),
            description=random.choice(fun_messages),
    )

    em.add_field(
            name="Account",
            value=character['accountName'],
            inline=True
            )

    em.add_field(
            name="League",
            value=character['league'],
            inline=True
            )

    em.add_field(
            name="Class",
            value=character['class'],
            inline=True
            )

    em.add_field(
            name="Level",
            value=character['level'],
            inline=True
            )

    em.add_field(
            name="Experience",
            value=f"{character['experience']:,d}",
            inline=True
            )

    em.add_field(
            name="Playtime",
            value=f"||{datetime.timedelta(seconds=int(character['stats']['playtime']))}||",
            inline=True
            )

    return em

def death_embed(character):
    """Given a mongodb character JSON, return a death embed
    """

    fun_messages = (
        "And then he *died*!",
        "AAAAAAaaaaagghhhhhh.....",
        "Zigged when he should have zagged",
        "Was that alchemy orb really worth it?",
        "They forgot to keep their HP > 0",
        "RNJesus said 'die'",
        "They rolled a natural 1",
        "Critical failure!",
        "Probably didn't learn their lesson..",
        "The enemy didn't accept their surrender...",
        "FATALITY",
        "They tripped and fell...",
        "They were caught cheating death...",
        "Didn't realize they were on their last life...",
        "They must be happy they can respawn...",
	"So, how was the dying?",
	"By using this New-U station, you have forfeited your right to reproduce.",
	"Between you and us, that thing that killed you is a total dick. Please disregard this message if you committed suicide.",
	"Do not worry about the afterlife, Hyperion customer! Hell is reserved exclusively for pedophiles, and people who buy Jakobs munitions.",
	"R-r-r-r-respawn!",
	"The Hyperion corporation is sure none of that was your fault.",
	"So long as you believe in yourself, nothing can TRULY kill you! Except Handsome Jack.",
	"Hyperion is not responsible for any fingers, toes, or breasts added during the respawn process.",
	"Dying is awesome! All of the cool kids are doing it!",
	"So, how are things?",
	"Oh, it's you again.",
	"Failed your saving throw, huh?",
	"At least you don't have to roll a new character.",
	"It's all fun and games until someone loses a kidney.",
	"Don't die now, you've still got quests to finish!",
	"At least the game's not too easy, right?",
	"Next time, you might wanna spend a healing surge.",
	"Just so you know, you're technically undead now.",
	"Lives? Where we're going we don't need lives.",
	"Death means nothing in this fantasy world!",
	"So, how does it feel to be a zombie?",
	"Are you Jesus?",
	"You might wanna put more points into life.",
	"Did you consider fighting something your own size?",
	"Keep Calm and Blame it on the Lag",
	"You could always respec.",
	"Maybe you need a tank to soak up some aggro.",
	"Here, have your hit points back!",
	"Maybe you should think about other games...",
	"Maybe you should play games you are good at...",
	"How about some checkers?",
	"That looked like it hurt.",
	"It's rise and shine time, maggot!",
	"Bummer, right?",
	"There's cheaper ways to get back to town...",
	"Why die when you could be productive?",
	"Better luck next time!",
	"You can do it!",
	"Good luck!",
	"Have a better one!",
	"We can always bring you back, unless you died in a cutscene.",
	"Death is but a temporary setback for the financially solvent.",
	"Side effects of resurrection include increased aggression, hoarding disorder, delusions of grandeur, and command hallucinations.",
	"Hey, you. You're finally awake. You were trying to cross the border, right?",
	"Let your resistances drop, did ya?",
	"I don't alawys get first place, but when I do, I'm on the losing team.",
	"DODGE!",
	"You know there are life flasks, right?",
	"How exactly did you expect that to end?",
	"You do know there isn't a deaths achievement, right?",
	"You know there isn't a deaths leaderboard, right?",
	"What ever you just tried, don't do that again",
	"What ever you just started doing, stop that",
        )

    em = discord.Embed(
            color = discord.Color.dark_red(),
            title=character['name'],
            timestamp=datetime.datetime.now(),
            description=random.choice(fun_messages),
    )

    em.add_field(
            name="Account",
            value=character['accountName'],
            inline=True
            )

    em.add_field(
            name="League",
            value=character['league'],
            inline=True
            )

    em.add_field(
            name="Class",
            value=character['class'],
            inline=True
            )

    em.add_field(
            name="Level",
            value=character['level'],
            inline=True
            )

    em.add_field(
            name="Experience",
            value=f"{character['experience']:,d}",
            inline=True
            )

    em.add_field(
            name="Playtime",
            value=f"||{datetime.timedelta(seconds=int(character['stats']['playtime']))}||",
            inline=True
            )

    em.add_field(
            name="XP", 
            value=f"`{xp_math.XPMath().xp_bar(character['experience'])}`",
            inline=False
            )

    return em
