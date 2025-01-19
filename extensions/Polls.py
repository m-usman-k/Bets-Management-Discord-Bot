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
        
    @app_commands.command(name="points" , description="Check the amount of points in your wallet.")
    async def points(self, interaction: discord.Interaction , user: discord.User = None):
        if user is None:
            user = interaction.user
            
        self.db.add_user(userid=user.id, username=user.name)
        points = self.db.get_user_points(userid=user.id)
        
        embed = discord.Embed(title="User Points" , description=None , color=discord.Color.blurple())
        embed.add_field(name="Userid:" , value=f"`{user.id}`" , inline=False)
        embed.add_field(name="Username:" , value=f"`{user.name}`" , inline=False)
        embed.add_field(name="Points:" , value=f"`{points}`" , inline=False)
        
        await interaction.response.send_message(embed=embed)
        
        
        
    @app_commands.command(name="add-points" , description="For admins to add points to users.")
    async def add_points(self, interaction: discord.Interaction, user: discord.User, points: int):
        
        self.db.add_user(userid=user.id, username=user.name)
        self.db.add_points(userid=user.id, points=points)
        
        points = self.db.get_user_points(userid=user.id)
        
        embed = discord.Embed(title="User Points Addition" , description=None , color=discord.Color.blurple())
        embed.add_field(name="Userid:" , value=f"`{user.id}`" , inline=False)
        embed.add_field(name="Username:" , value=f"`{user.name}`" , inline=False)
        embed.add_field(name="Points:" , value=f"`{points}`" , inline=False)
        
        await interaction.response.send_message(embed=embed)

        
    @app_commands.command(name="rem-points" , description="For admins to remove points from users.")
    async def rem_points(self, interaction: discord.Interaction, user: discord.User, points: int):
        
        self.db.add_user(userid=user.id, username=user.name)
        self.db.remove_points(userid=user.id, points=points)
        
        points = self.db.get_user_points(userid=user.id)
        
        embed = discord.Embed(title="User Points Removal" , description=None , color=discord.Color.blurple())
        embed.add_field(name="Userid:" , value=f"`{user.id}`" , inline=False)
        embed.add_field(name="Username:" , value=f"`{user.name}`" , inline=False)
        embed.add_field(name="Points:" , value=f"`{points}`" , inline=False)
        
        await interaction.response.send_message(embed=embed)
    
    
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