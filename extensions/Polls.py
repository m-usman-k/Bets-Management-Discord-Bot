import discord
import dotenv, os, time
from discord import app_commands
from discord.ext import commands
from functions.Database import Database

dotenv.load_dotenv()
MESSAGE_POINTS = int(os.getenv("MESSAGE_POINTS", 1))

class Polls(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database("./database/users.db")
        self.shop_items = []
        with open("./database/shop.txt", "r") as file:
            all_data = file.readlines()
            self.shop_items = [
                {"name": item.split(":")[0], "price": int(item.split(":")[1])} for item in all_data
            ]

    @app_commands.command(name="points", description="Check the amount of points in your wallet.")
    async def points(self, interaction: discord.Interaction, user: discord.User = None):
        if user is None:
            user = interaction.user

        self.db.add_user(userid=user.id, username=user.name)
        points = self.db.get_user_points(userid=user.id)

        embed = discord.Embed(title="User Points", description=None, color=discord.Color.blurple())
        embed.add_field(name="Userid:", value=f"`{user.id}`", inline=False)
        embed.add_field(name="Username:", value=f"`{user.name}`", inline=False)
        embed.add_field(name="Points:", value=f"`{points}`", inline=False)

        await interaction.response.send_message(embed=embed)

    @commands.has_permissions(administrator=True)
    @app_commands.command(name="add-points", description="For admins to add points to users.")
    async def add_points(self, interaction: discord.Interaction, user: discord.User, points: int):
        self.db.add_user(userid=user.id, username=user.name)
        self.db.add_points(userid=user.id, points=points)

        points = self.db.get_user_points(userid=user.id)

        embed = discord.Embed(title="User Points Addition", description=None, color=discord.Color.blurple())
        embed.add_field(name="Userid:", value=f"`{user.id}`", inline=False)
        embed.add_field(name="Username:", value=f"`{user.name}`", inline=False)
        embed.add_field(name="Points:", value=f"`{points}`", inline=False)

        await interaction.response.send_message(embed=embed)

    @commands.has_permissions(administrator=True)
    @app_commands.command(name="rem-points", description="For admins to remove points from users.")
    async def rem_points(self, interaction: discord.Interaction, user: discord.User, points: int):
        self.db.add_user(userid=user.id, username=user.name)
        self.db.remove_points(userid=user.id, points=points)

        points = self.db.get_user_points(userid=user.id)

        embed = discord.Embed(title="User Points Removal", description=None, color=discord.Color.blurple())
        embed.add_field(name="Userid:", value=f"`{user.id}`", inline=False)
        embed.add_field(name="Username:", value=f"`{user.name}`", inline=False)
        embed.add_field(name="Points:", value=f"`{points}`", inline=False)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="shop", description="Display shop prices.")
    async def shop(self, interaction: discord.Interaction):
        embed = discord.Embed(title="Shop Prices", color=discord.Color.green())
        for item in self.shop_items:
            embed.add_field(name=item["name"], value=f"{item['price']} points", inline=False)

        await interaction.response.send_message(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        user_id = message.author.id
        username = message.author.name

        self.db.add_user(user_id, username)
        self.db.add_points(user_id, MESSAGE_POINTS)  # Add points for each message

        await self.bot.process_commands(message)
        
    @app_commands.command(name="leaderboard", description="Display the top 10 users by points.")
    async def leaderboard(self, interaction: discord.Interaction):
        top_users = self.db.get_top_users(limit=10)
        if not top_users:
            await interaction.response.send_message("No users found.", ephemeral=True)
            return

        embed = discord.Embed(title="Leaderboard", color=discord.Color.gold())
        for index, (username, points) in enumerate(top_users, start=1):
            embed.add_field(name=f"{index}. {username}", value=f"`{points} points`", inline=False)

        await interaction.response.send_message(embed=embed)

    @commands.has_permissions(administrator=True)
    @app_commands.command(name="end-poll", description="To decide the result of the poll and end it.")
    async def end_poll(self, interaction: discord.Interaction, poll_id: str):
        poll_id = int(poll_id)
        if not self.db.poll_exists(poll_id):
            await interaction.response.send_message("Poll does not exist.", ephemeral=True)
            return

        self.db.cursor.execute("SELECT question, first_option, second_option, first_joinees, second_joinees, is_active FROM polls WHERE pollid = ?", (poll_id,))
        poll = self.db.cursor.fetchone()
        if not poll:
            await interaction.response.send_message("Poll not found.", ephemeral=True)
            return

        question, first_option, second_option, first_joinees, second_joinees, is_active = poll

        if not is_active:
            await interaction.response.send_message("This poll has already been ended.", ephemeral=True)
            return

        class PollDropdown(discord.ui.Select):
            def __init__(self):
                options = [
                    discord.SelectOption(label=first_option, description="Select this option as the winner"),
                    discord.SelectOption(label=second_option, description="Select this option as the winner")
                ]
                super().__init__(placeholder="Choose the winning option...", min_values=1, max_values=1, options=options)

            async def callback(self, interaction: discord.Interaction):

                self.view.selected_option = self.values[0]
                winning_option = self.view.selected_option
                if winning_option == first_option:
                    winning_joinees = first_joinees
                    losing_joinees = second_joinees
                else:
                    winning_joinees = second_joinees
                    losing_joinees = first_joinees

                total_losing_points = sum(int(bet.split(":")[1]) for bet in losing_joinees.split(",") if bet)
                winning_users = [bet.split(":") for bet in winning_joinees.split(",") if bet]

                for user_id, bet_amount in winning_users:
                    user_id = int(user_id)
                    bet_amount = int(bet_amount)
                    dividend = bet_amount + (total_losing_points * (bet_amount / sum(int(bet.split(":")[1]) for bet in winning_joinees.split(",") if bet)))
                    self.view.db.add_points(user_id, int(dividend))

                self.view.db.set_poll_inactive(poll_id)

                # Calculate percentages and number of voters
                total_votes = len(first_joinees.split(",")) + len(second_joinees.split(","))
                first_option_votes = len(first_joinees.split(",")) if first_joinees else 0
                second_option_votes = len(second_joinees.split(",")) if second_joinees else 0

                first_option_percentage = (first_option_votes / total_votes) * 100 if total_votes > 0 else 0
                second_option_percentage = (second_option_votes / total_votes) * 100 if total_votes > 0 else 0

                embed = discord.Embed(title="Poll Ended", description=f"The winning option is: {winning_option}", color=discord.Color.green())
                embed.add_field(name="Winning Joinees", value=winning_joinees, inline=False)
                embed.add_field(name="Losing Joinees", value=losing_joinees, inline=False)
                embed.add_field(name=f"{first_option} Votes", value=f"{first_option_votes} ({first_option_percentage:.2f}%)", inline=True)
                embed.add_field(name=f"{second_option} Votes", value=f"{second_option_votes} ({second_option_percentage:.2f}%)", inline=True)
                await interaction.response.send_message(embed=embed, ephemeral=True)

        class PollDropdownView(discord.ui.View):
            def __init__(self, db):
                super().__init__()
                self.db = db
                self.selected_option = None
                self.add_item(PollDropdown())

        embed = discord.Embed(title=f"End Poll: {question}", description="Select the winning option", color=discord.Color.blue())
        embed.add_field(name="Option 1", value=first_option, inline=False)
        embed.add_field(name="Option 2", value=second_option, inline=False)

        await interaction.response.send_message(embed=embed, view=PollDropdownView(self.db), ephemeral=True)

    @commands.has_permissions(administrator=True)
    @app_commands.command(name="create-poll", description="For admins to create a poll.")
    async def create_poll(self, interaction: discord.Interaction, question: str, first_option: str, second_option: str, expiry_time_hours: int, channel: discord.TextChannel):
        if interaction.user.guild_permissions.administrator:
            message = await interaction.response.defer(ephemeral=True)
            embed = discord.Embed(title=question, description=None, color=discord.Color.blurple())
            embed.add_field(name="Option 1:", value=first_option, inline=False)
            embed.add_field(name="Option 2:", value=second_option, inline=False)

            embed.set_image(url="https://www.ovationmr.com/wp-content/uploads/2021/09/Poll-vs.-Survey.webp")

            async def button_callback(button_interaction: discord.Interaction):
                if not self.db.poll_not_expired(pollid=button_interaction.message.id):
                    return await interaction.response.send_message(content="The Poll Has Expired!", ephemeral=True)

                self.db.add_user(userid=button_interaction.user.id, username=button_interaction.user.name)
                button_custom_id = button_interaction.data["custom_id"]
                poll_id = button_interaction.message.id

                if self.db.poll_not_expired(pollid=poll_id):
                    value_modal = ValueModal(button_custom_id=button_custom_id, user_points=self.db.get_user_points(button_interaction.user.id), db=self.db, pollid=poll_id)
                    await button_interaction.response.send_modal(value_modal)
                else:
                    await button_interaction.response.send_message("Poll has expired.", ephemeral=True)

            first_option_button = discord.ui.Button(label=first_option, custom_id=f"{first_option}", style=discord.ButtonStyle.blurple)
            second_option_button = discord.ui.Button(label=second_option, custom_id=second_option, style=discord.ButtonStyle.blurple)

            first_option_button.callback = button_callback
            second_option_button.callback = button_callback

            view = discord.ui.View()
            view.add_item(first_option_button)
            view.add_item(second_option_button)

            new_poll = await channel.send(embed=embed, view=view)
            print(new_poll.id)
            self.db.add_poll(pollid=new_poll.id, question=question, first_option=first_option, second_option=second_option, expiry_time_hours=int(time.time() + (expiry_time_hours * 60 * 60)), is_active=1)
            await interaction.followup.send(content=f"Poll Created Successfully In {channel.mention}", ephemeral=True)
        else:
            await interaction.response.send_message(content="You don't have the required permissions to perform this action.", ephemeral=True)

class ValueModal(discord.ui.Modal):
    def __init__(self, button_custom_id: str, user_points: int, db: Database, pollid: int):
        self.db = db
        self.pollid = pollid
        self.user_points = user_points
        self.button_custom_id = button_custom_id
        super().__init__(title="Enter your bet amount")

        self.add_item(discord.ui.TextInput(
            label="Enter a positive integer",
            placeholder="Type a number here...",
            custom_id="integer_input",
            required=True,
            style=discord.TextStyle.short,
        ))

    async def on_submit(self, interaction: discord.Interaction):
        user_input = self.children[0].value

        if user_input.isdigit():
            number = int(user_input)

            if number > self.user_points:
                await interaction.response.send_message(content="You don't have enough points to perform this action.", ephemeral=True)
            else:
                response = self.db.add_user_to_poll(userid=interaction.user.id, poll_option=self.button_custom_id, pollid=self.pollid, bet_amount=number)
                if response == 2:
                    return await interaction.response.send_message(content="You have already voted in this poll.", ephemeral=True)

                self.db.remove_points(userid=interaction.user.id, points=number)

                await interaction.response.send_message(content=f"You have bet {number} points on {self.button_custom_id}", ephemeral=True)

        else:
            await interaction.response.send_message(
                "Invalid input! Please enter a valid integer.", ephemeral=True
            )

    async def on_cancel(self, interaction: discord.Interaction):
        await interaction.response.send_message("You cancelled the modal.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Polls(bot))