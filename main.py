import dotenv
import discord, os
from discord.ext import commands

# Globals and envs:
dotenv.load_dotenv('.env')

BOT_TOKEN = os.getenv('BOT_TOKEN')

# All other processing:
bot = commands.Bot(command_prefix="!" , intents=discord.Intents().all())

@bot.event
async def on_ready():
    
    await bot.load_extension("extensions.Bets")
    
    await bot.tree.sync()


# Running related things:
bot.run(BOT_TOKEN)