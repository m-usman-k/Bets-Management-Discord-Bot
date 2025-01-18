import discord
import dotenv, os
from discord import app_commands
from discord.ext import commands
from functions.Database import Database

dotenv.load_dotenv()
MESSAGE_POINTS = os.getenv("MESSAGE_POINTS")

class Polls(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database("./database/users.db")
        
    @app_commands.command(name="create-poll" , description="For admins to create a poll.")
    async def create_poll(self, interaction: discord.Interaction):
        button = discord.ui.Button(label="Test Button")

        async def button_callback(interaction):
            await interaction.response.send_message("Button clicked!", ephemeral=True)
            
        button.callback = button_callback
        view = discord.ui.View()
        view.add_item(button)
        await interaction.response.send_message(view=view)
        
    
async def setup(bot):
    await bot.add_cog(Polls(bot))