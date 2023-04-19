import os, json, asyncio, discord, logging, coloredlogs, locale

from discord.ext import commands
from dotenv import load_dotenv
from jours_feries_france import JoursFeries

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from crontab import CronTab
from datetime import datetime, timedelta

from models.base import Base
from models.cron import Cron
from models.user import User
from models.schedule import Schedule
from models.buttons import Buttons

load_dotenv()

coloredlogs.install(level='DEBUG')

locale.setlocale(locale.LC_ALL, 'fr_FR.UTF-8')

tasks = []

# -------------------------------- Bot Setup --------------------------------

class PesistentBot(commands.Bot):
	def __init__(self):
		intents = discord.Intents.default()
		intents.members = True
		intents.message_content = True

		super().__init__(intents=intents, command_prefix="JeSuisDisabled", case_insensitive=True)

	async def setup_hook(self):
		self.add_view(Buttons())
		self.add_view(SingleButton())

	async def on_ready(self):
		global tasks
		await self.tree.sync()
		# restart cron from file
		session = Session()
		crons = Cron.get_all(session)
		for cron in crons:
			channel = self.get_channel(cron.channel_id)
			logging.debug(msg=f"Restarting cron job with interval `{cron.interval}` for channel `{cron.channel_id}` on server `{channel.guild}`")
			tasks.append(self.loop.create_task(send_schedule(cron.interval, channel), name=f"{channel.id}"))
		logging.info(f'We have logged in as {self.user}')

bot = PesistentBot()

# --------------------------------- Commands ---------------------------------

# ------------------ Schedule management ------------------

@bot.tree.command(name = "start_schedule", description = "Start schedule cron in this channel")
@discord.app_commands.default_permissions(administrator=True)
async def schedule(interaction: discord.Interaction, interval: str):
	global tasks
	logging.debug(f"User {interaction.user} request start schedule cron in channel `{interaction.channel}` with interval `{interval}` on server `{interaction.guild}`")
	if interaction.user.guild_permissions.administrator:
		logging.debug(f"Tasks : {[int(task.get_name()) for task in tasks]}")
		if interaction.channel.id not in [int(task.get_name()) for task in tasks]:
			logging.debug(f"Starting cron job in {interaction.channel_id}")
			try:
				session = Session()
				session.add(Cron(channel_id=interaction.channel_id, interval=interval))
				session.commit()
				session.close()
				tasks.append(bot.loop.create_task(send_schedule(interval, interaction.channel), name=f'{interaction.channel_id}'))
				await interaction.response.send_message(f"Saving this channel for cron job `{interval}`")
			except Exception as e:
				logging.error(f"Error while adding cron job to database : {e}")
		else:
			await interaction.response.send_message(f"This channel as already a cron job")
	else:
		await interaction.response.send_message(f"You need to be an administrator to use this command", ephemeral=True)

@bot.tree.command(name = "list_schedules", description = "List all planned cron")
@discord.app_commands.default_permissions(administrator=True)
async def list_schedules(interaction: discord.Interaction):
	logging.debug(f"User {interaction.user} request list planned cron on server `{interaction.guild}`")
	if interaction.user.guild_permissions.administrator:
		session = Session()
		if len(session.query(Cron).all()) > 0:
			await interaction.response.send_message(embed=Cron.get_all_embed(session))
		else:
			await interaction.response.send_message(f"No planned cron")
	else:
		await interaction.response.send_message(f"You need to be an administrator to use this command", ephemeral=True)


@bot.tree.command(name = "stop_schedule", description = "Stop planned cron in this channel")
@discord.app_commands.default_permissions(administrator=True)
async def stop(interaction: discord.Interaction):
	global tasks
	logging.debug(f"User {interaction.user} request stop planning cron in channel {interaction.channel} <#{interaction.channel_id}>")
	if (interaction.user.guild_permissions.administrator):
		logging.debug(f"Tasks : {[int(task.get_name()) for task in tasks]}")
		if (interaction.channel_id in [int(task.get_name()) for task in tasks]):
			logging.debug(f"Stopping cron job in {interaction.channel_id}")
			session = Session()
			session.delete(Cron.get_by_channel_id(session, interaction.channel_id))
			session.commit()
			session.close()
			for task in tasks:
				if task.get_name() == str(interaction.channel_id):
					task.cancel()
					tasks.remove(task)
					break
			await interaction.response.send_message(f"Stopping any cron job in this channel")
		else:
			await interaction.response.send_message(f"No cron job in this channel")
	else:
		await interaction.response.send_message(f"You are not an administrator", ephemeral=True)


		await interaction.response.defer()
# ------------------ User management ------------------

@bot.tree.command(name="add_user", description="Add a new user")
@discord.app_commands.default_permissions(administrator=True)
async def add_user(interaction: discord.Interaction, discord_user: discord.User, first_name: str, last_name: str, login: str):
	logging.debug(f"User {interaction.user} request add user {login} with discord id {discord_user.id}")
	if (interaction.user.guild_permissions.administrator):
		session = Session()
		session.add(User(discord_id=discord_user.id, first_name=first_name, last_name=last_name, login=login))
		session.commit()
		session.close()
		await interaction.response.send_message(f"User `{login}` added with discord id <@{discord_user.id}>")
	else:
		await interaction.response.send_message(f"You are not an administrator", ephemeral=True)

@bot.tree.command(name="disable_user", description="Disable a user")
@discord.app_commands.default_permissions(administrator=True)
async def remove_user(interaction: discord.Interaction, login: str):
	logging.debug(f"User {interaction.user} request disable for user {login}")
	if (interaction.user.guild_permissions.administrator):
		session = Session()
		user = User.get_by_login(session, login)
		if user:
			session.delete(user)
			session.commit()
		session.close()
		await interaction.response.send_message(f"User `{login}` disabled", ephemeral=True)
	else:
		await interaction.response.send_message(f"You are not an administrator", ephemeral=True)

@bot.tree.command(name="rename_user", description="Rename a user")
@discord.app_commands.default_permissions(administrator=True)
async def rename_user(interaction: discord.Interaction, login: str, new_login: str):
	logging.debug(f"User {interaction.user} request rename user {login} to {new_login}")
	if (interaction.user.guild_permissions.administrator):
		session = Session()
		user = User.get_by_login(session, login)
		if user:
			user.login = new_login
			session.commit()
		session.close()
		await interaction.response.send_message(f"User `{login}` renamed to `{new_login}`")
	else:
		await interaction.response.send_message(f"You are not an administrator", ephemeral=True)

@bot.tree.command(name="list_users", description="List all users")
@discord.app_commands.default_permissions(administrator=True)
async def list_users(interaction: discord.Interaction):
	logging.debug(f"User {interaction.user} request list users")
	if (interaction.user.guild_permissions.administrator):
		session = Session()
		await interaction.response.send_message(embed=User.get_all_embed(session))
		session.close()
	else:
		await interaction.response.send_message(f"You are not an administrator", ephemeral=True)

# ------------------ Cron job ------------------
def number_to_emoji(number):
	return [ "0️⃣", "1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟" ][number]

class SingleButton(discord.ui.View):
	def __init__(self):
		super().__init__(timeout=None)

	@discord.ui.button(label="Matin", style=discord.ButtonStyle.green, custom_id="matin")
	async def morning(self, interaction: discord.Interaction, button: discord.ui.Button):
		await interaction.response.defer()
		session = Session()
		date = datetime.strptime(interaction.message.embeds[0].title, "%a %d %B %Y")
		user = User.get_by_discord_id(session, interaction.user.id)
		if user and user.active:
			schedule = Schedule.switch_morning(session, user.id, date)
			schedules = Schedule.get_by_date(session, date)
			logging.debug(f"List Schedules: {schedules}")
			edited_embed = interaction.message.embeds[0]
			edited_embed.set_field_at(0, name="Matin", value="\n".join([ f"{number_to_emoji(i+1)} {schedule.user.login}" for i, schedule in enumerate(schedules) if schedule.morning ]))
			await interaction.message.edit(embed=edited_embed)
		session.close()


	@discord.ui.button(label="Après-midi", style=discord.ButtonStyle.green, custom_id="apres-midi")
	async def afternoon(self, interaction: discord.Interaction, button: discord.ui.Button):
		await interaction.response.defer()
		session = Session()
		date = datetime.strptime(interaction.message.embeds[0].title, "%a %d %B %Y")
		user = User.get_by_discord_id(session, interaction.user.id)
		if user and user.active:
			schedule = Schedule.switch_afternoon(session, user.id, date)
			schedules = Schedule.get_by_date(session, date)
			logging.debug(f"List Schedules: {schedules}")
			edited_embed = interaction.message.embeds[0]
			edited_embed.set_field_at(1, name="Après-midi", value="\n".join([ f"{number_to_emoji(i+1)} {schedule.user.login}" for i, schedule in enumerate(schedules) if schedule.afternoon ]))
			await interaction.message.edit(embed=edited_embed)
		session.close()

@bot.tree.command(name="test", description="Test command")
async def test(interaction: discord.Interaction):
	await interaction.response.defer(ephemeral=True, thinking=False)
	now = datetime.now()
	lundi = now + timedelta(days=(-now.weekday())+7)

	embeds = []
	session = Session()
	for i in range(0, 5):
		day = lundi + timedelta(days=i)
		schedule = Schedule.get_by_date(session, day)
		# Color gradient
		bank = JoursFeries.is_bank_holiday(day, zone="Métropole")
		embed = discord.Embed(title=day.strftime("%a %d %B %Y"), color=[0x00FFFF, 0xFF0000][bank])
		embed.add_field(name="Matin", value="\n".join([ f"{number_to_emoji(i+1)} {schedule.user.login}" for i, schedule in enumerate(schedule) if schedule.morning ]))
		embed.add_field(name="Après-midi", value="\n".join([ f"{number_to_emoji(i+1)} {schedule.user.login}" for i, schedule in enumerate(schedule) if schedule.afternoon ]))
		if bank:
			embed.set_footer(text="Jour férié")
		if bank:
			await interaction.channel.send(embed=embed)
		else:
			await interaction.channel.send(embed=embed, view=SingleButton())
	session.close()

if __name__ == "__main__":
	logging.info("Starting...")
	# engine = create_engine('postgresql://benevoles:toto42@postgres/postgres')
	engine = create_engine('sqlite:///planning.db')
	Base.metadata.create_all(engine)
	Session = sessionmaker(bind=engine)
	bot.run(os.environ.get('DISCORD_TOKEN'))