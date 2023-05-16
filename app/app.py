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
from models.exception import ExceptionDay

load_dotenv()

if os.getenv("DEBUG") == "True":
	coloredlogs.install(level='DEBUG')
else:
	coloredlogs.install(level='INFO')

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
			logging.info(msg=f"Restarting cron job with interval `{cron.interval}` for channel `{channel}` on server `{channel.guild}`")
			tasks.append(self.loop.create_task(auto_schedule(cron.interval, channel), name=f"{channel.id}"))
		logging.info(f'We have logged in as {self.user}')

bot = PesistentBot()

# --------------------------------- Commands ---------------------------------

# ------------------ Schedule management ------------------

@bot.tree.command(name = "start_schedule", description = "Start schedule cron in this channel")
@discord.app_commands.default_permissions(administrator=True)
async def start_schedule(interaction: discord.Interaction, interval: str):
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
				tasks.append(bot.loop.create_task(auto_schedule(interval, interaction.channel), name=f'{interaction.channel_id}'))
				await interaction.response.send_message(f"Saving this channel for cron job `{interval}`")
			except Exception as e:
				logging.error(f"Error while adding cron job to database : {e}")
		else:
			await interaction.response.send_message(f"This channel as already a cron job", ephemeral=True)
	else:
		await interaction.response.send_message(f"You need to be an administrator to use this command", ephemeral=True)

@bot.tree.command(name = "list_schedules", description = "List all planned cron")
@discord.app_commands.default_permissions(administrator=True)
async def list_schedules(interaction: discord.Interaction):
	logging.debug(f"User {interaction.user} request list planned cron on server `{interaction.guild}`")
	if interaction.user.guild_permissions.administrator:
		session = Session()
		if len(session.query(Cron).all()) > 0:
			await interaction.response.send_message(embed=Cron.get_all_embed(session), ephemeral=True)
		else:
			await interaction.response.send_message(f"No planned cron", ephemeral=True)
	else:
		await interaction.response.send_message(f"You need to be an administrator to use this command", ephemeral=True)


@bot.tree.command(name = "stop_schedule", description = "Stop planned cron in this channel")
@discord.app_commands.default_permissions(administrator=True)
async def stop_schedule(interaction: discord.Interaction):
	global tasks
	logging.info(f"User {interaction.user} request stop planning cron in channel {interaction.channel} <#{interaction.channel_id}>")
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
			await interaction.response.send_message(f"Stopping any cron job in this channel", ephemeral=True)
		else:
			await interaction.response.send_message(f"No cron job in this channel", ephemeral=True)
	else:
		await interaction.response.send_message(f"You are not an administrator", ephemeral=True)

# ------------------ User management ------------------

async def get_active_users_autocomplete(interaction: discord.Integration, current: str) -> list[discord.app_commands.Choice[str]]:
	try:
		session = Session()
		users = User.get_all_active_partial(session, current)
		logging.debug(f"Autocomplete for user {current} : {users}")
		session.close()
		if users:
			return [discord.app_commands.Choice(name=user.login, value=user.login) for user in users]
		return [discord.app_commands.Choice(name="No user found", value="")]
	except Exception as e:
		logging.error(f"Error while getting users for autocomplete : {e}")

async def get_disabled_users_autocomplete(interaction: discord.Integration, current: str) -> list[discord.app_commands.Choice[str]]:
	try:
		session = Session()
		users = User.get_all_disabled_partial(session, current)
		logging.debug(f"Autocomplete for user {current} : {users}")
		logging.debug(f"{User.get_all(session)}")
		session.close()
		if users:
			return [discord.app_commands.Choice(name=user.login, value=user.login) for user in users]
		return [discord.app_commands.Choice(name="No user found", value="")]
	except Exception as e:
		logging.error(f"Error while getting users for autocomplete : {e}")

async def get_users_autocomplete(interaction: discord.Integration, current: str) -> list[discord.app_commands.Choice[str]]:
	try:
		session = Session()
		users = User.get_all_partial(session, current)
		logging.debug(f"Autocomplete for user {current} : {users}")
		session.close()
		if users:
			return [discord.app_commands.Choice(name=user.login, value=user.login) for user in users]
		return [discord.app_commands.Choice(name="No user found", value="")]
	except Exception as e:
		logging.error(f"Error while getting users for autocomplete : {e}")

@bot.tree.command(name="add_user", description="Add a new user")
@discord.app_commands.default_permissions(administrator=True)
async def add_user(interaction: discord.Interaction, discord_user: discord.User, first_name: str, last_name: str, login: str):
	logging.debug(f"User {interaction.user} request add user {login} with discord id {discord_user.id}")
	session = Session()
	try:
		session.add(User(discord_id=discord_user.id, first_name=first_name, last_name=last_name, login=login))
		session.commit()
		await interaction.response.send_message(f"User `{login}` added with discord id <@{discord_user.id}>", ephemeral=True)
	except Exception as e:
		logging.error(f"Error while adding user to database : {e}")
		await interaction.response.send_message(f"Error while adding user to database : {e}", ephemeral=True)
	session.close()

@bot.tree.command(name="disable_user", description="Disable a user")
@discord.app_commands.default_permissions(administrator=True)
@discord.app_commands.autocomplete(login=get_active_users_autocomplete)
async def remove_user(interaction: discord.Interaction, login: str):
	logging.info(f"User {interaction.user} request disable for user {login}")
	session = Session()
	user = User.get_by_login(session, login)
	if user:
		user.active = False
		session.commit()
	session.close()
	await interaction.response.send_message(f"User `{login}` disabled", ephemeral=True)

@bot.tree.command(name="enable_user", description="Enable a user")
@discord.app_commands.default_permissions(administrator=True)
@discord.app_commands.autocomplete(login=get_disabled_users_autocomplete)
async def enable_user(interaction: discord.Interaction, login: str):
	logging.info(f"User {interaction.user} request enable for user {login}")
	session = Session()
	user = User.get_by_login(session, login)
	if user:
		user.active = True
		session.commit()
	session.close()
	await interaction.response.send_message(f"User `{login}` enabled", ephemeral=True)

@bot.tree.command(name="rename_user", description="Rename a user")
@discord.app_commands.default_permissions(administrator=True)
@discord.app_commands.autocomplete(login=get_active_users_autocomplete)
async def rename_user(interaction: discord.Interaction, login: str, new_login: str):
	logging.info(f"User {interaction.user} request rename user {login} to {new_login}")
	session = Session()
	user = User.get_by_login(session, login)
	if user:
		user.login = new_login
		session.commit()
	session.close()
	await interaction.response.send_message(f"User `{login}` renamed to `{new_login}`", ephemeral=True)

@bot.tree.command(name="delete_user", description="Delete a user")
@discord.app_commands.default_permissions(administrator=True)
@discord.app_commands.autocomplete(login=get_users_autocomplete)
async def delete_user(interaction: discord.Interaction, login: str):
	logging.info(f"User {interaction.user} request delete user {login}")
	session = Session()
	user = User.get_by_login(session, login)
	if user:
		session.delete(user)
		session.commit()
	session.close()
	await interaction.response.send_message(f"User `{login}` deleted", ephemeral=True)

@bot.tree.command(name="list_users", description="List all users")
@discord.app_commands.default_permissions(administrator=True)
async def list_users(interaction: discord.Interaction):
	logging.info(f"User {interaction.user} request list users")
	session = Session()
	await interaction.response.send_message(embed=User.get_all_embed(session))
	session.close()

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
			schedule = Schedule.switch_morning(session, str(user.id), date)
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
			schedule = Schedule.switch_afternoon(session, str(user.id), date)
			schedules = Schedule.get_by_date(session, date)
			logging.debug(f"List Schedules: {schedules}")
			edited_embed = interaction.message.embeds[0]
			edited_embed.set_field_at(1, name="Après-midi", value="\n".join([ f"{number_to_emoji(i+1)} {schedule.user.login}" for i, schedule in enumerate(schedules) if schedule.afternoon ]))
			await interaction.message.edit(embed=edited_embed)
		session.close()

async def send_schedule(channel, lundi):
	try:
		embeds = []
		session = Session()
		for i in range(0, 5):
			day = lundi + timedelta(days=i)
			schedule = Schedule.get_by_date(session, day)
			# Color gradient
			bank = JoursFeries.is_bank_holiday(day, zone="Métropole")
			if (not bank):
				exceptionDay = ExceptionDay.get_by_date(session, day) is not None
			embed = discord.Embed(title=day.strftime("%a %d %B %Y"), color=[0x00FFFF, 0xFF0000][bank|exceptionDay])
			embed.add_field(name="Matin", value="\n".join([ f"{number_to_emoji(i+1)} {schedule.user.login}" for i, schedule in enumerate(schedule) if schedule.morning ]))
			embed.add_field(name="Après-midi", value="\n".join([ f"{number_to_emoji(i+1)} {schedule.user.login}" for i, schedule in enumerate(schedule) if schedule.afternoon ]))
			if bank:
				embed.set_footer(text="Jour férié")
			if exceptionDay:
				embed.set_footer(text="Exception")
			if bank or exceptionDay:
				await channel.send(embed=embed)
			else:
				await channel.send(embed=embed, view=SingleButton())
		session.close()
	except Exception as e:
		logging.error(e)

async def auto_schedule(interval, channel):
	try:
		await bot.wait_until_ready()
		cron = CronTab(interval)
		logging.debug(f"Start cron job {interval} for channel {channel}")
		while not bot.is_closed():
			await asyncio.sleep(cron.next(default_utc=True))
			now = datetime.now()
			await send_schedule(channel, now + timedelta(days=(-now.weekday())+7))
	except asyncio.CancelledError:
		logging.debug(f"Stop cron job {interval} for channel {channel}")

@bot.tree.command(name="manual_schedule", description="Send the schedule for the selected week")
@discord.app_commands.default_permissions(administrator=True)
@discord.app_commands.describe(lundi="Date du lundi de la semaine à afficher (format: JJ/MM/AAAA)")
async def manual_schedule(interaction: discord.Interaction, lundi: str):
	now = datetime.now()
	lundi = datetime.strptime(lundi, "%d/%m/%Y")
	if lundi.weekday() != 0:
		await interaction.response.send_message("La date doit être un lundi", ephemeral=True)
		return
	await interaction.response.defer(ephemeral=True, thinking=False)
	await send_schedule(interaction.channel, lundi)

# ------------------ Exceptions ------------------

async def date_list_auto_complete(interaction: discord.Integration, current: str) -> list[discord.app_commands.Choice[str]]:
	session = Session()
	days = ExceptionDay.get_by_partial_date_as_list(session, current)
	logging.debug(f"List days: {days}")
	for day in days:
		logging.debug(f"Day: {datetime.strftime(day, '%d/%m/%Y')}")
	session.close()
	if days:
		return [ discord.app_commands.Choice(name=datetime.strftime(day, "%d/%m/%Y"), value=datetime.strftime(day, "%d/%m/%Y")) for day in days ]
	else:
		return [ discord.app_commands.Choice(name="No result", value="") ]

@bot.tree.command(name="add_exception", description="Add an exception day")
@discord.app_commands.default_permissions(administrator=True)
@discord.app_commands.describe(date="Date of the exception day (DD/MM/YYYY)")
async def add_exception(interaction: discord.Interaction, date: str):
	logging.info(f"User {interaction.user} request add exception")
	if (interaction.user.guild_permissions.administrator):
		date = datetime.strptime(date, "%d/%m/%Y")
		session = Session()
		try:
			exception = ExceptionDay(date=date)
			session.add(exception)
			session.commit()
			await interaction.response.send_message(f"Exception added: {exception}")
		except Exception as e:
			await interaction.response.send_message(f"Error: {e}", ephemeral=True)
		session.close()
	else:
		await interaction.response.send_message(f"You are not an administrator", ephemeral=True)

@bot.tree.command(name="remove_exception", description="Remove an exception day")
@discord.app_commands.default_permissions(administrator=True)
@discord.app_commands.autocomplete(date=date_list_auto_complete)
@discord.app_commands.describe(date="Date of the exception day (DD/MM/YYYY)")
async def remove_exception(interaction: discord.Interaction, date: str):
	logging.info(f"User {interaction.user} request remove exception")
	if (interaction.user.guild_permissions.administrator):
		date = datetime.strptime(date, "%d/%m/%Y")
		session = Session()
		try:
			exception = ExceptionDay.get_by_date(session, date.date())
			if exception:
				session.delete(exception)
				session.commit()
				await interaction.response.send_message(f"Exception removed: {exception}")
			else:
				await interaction.response.send_message(f"Exception not found: {date.date()}", ephemeral=True)
		except Exception as e:
			await interaction.response.send_message(f"Error: {e}", ephemeral=True)
		session.close()
	else:
		await interaction.response.send_message(f"You are not an administrator", ephemeral=True)

# ------------------ Export ------------------

@bot.tree.command(name="export", description="Export the planning to a CSV file")
@discord.app_commands.default_permissions(administrator=True)
@discord.app_commands.describe(start_date="Start date of the export (DD/MM/YYYY)", end_date="End date of the export (DD/MM/YYYY)")
async def export(interaction: discord.Interaction, start_date: str, end_date: str):
	logging.info(f"User {interaction.user} request export")
	session = Session()
	try:
		planning = Schedule.get_by_date_range(session, datetime.strptime(start_date, "%d/%m/%Y"), datetime.strptime(end_date, "%d/%m/%Y"))
		# parse planning to dict with date as key, and list of users as value
		planning_dict = {}
		users = []
		for schedule in planning:
			if schedule.date not in planning_dict:
				planning_dict[schedule.date] = {"morning": [], "afternoon": []}
			if schedule.morning:
				planning_dict[schedule.date]["morning"].append(schedule.user)
			if schedule.afternoon:
				planning_dict[schedule.date]["afternoon"].append(schedule.user)
			if schedule.user not in users:
				users.append(schedule.user)
		planning_dict = dict(sorted(planning_dict.items()))
		logging.debug(f"Planning dict: {planning_dict}")

		# Create the CSV file
		with open("planning.csv", "w") as file:
			file.write("Date;Matin;")
			for i in range(len(users) - 1):
				file.write(";")
			file.write("Apres-midi")
			for i in range(len(users) - 1):
				file.write(";")
			file.write("\n;")
			for i in range(2):
				for user in users:
					file.write(f"{user.login};")
			file.write("\n")
			# Write the planning
			for date in planning_dict:
				file.write(f"{datetime.strftime(date, '%d/%m/%Y')};")
				for user in users:
					if user in planning_dict[date]["morning"]:
						file.write("True;")
					else:
						file.write("False;")
				for user in users:
					if user in planning_dict[date]["afternoon"]:
						file.write("True;")
					else:
						file.write("False;")
				file.write("\n")
		# Send the file
		await interaction.response.send_message("Export done", file=discord.File("planning.csv"))
	except Exception as e:
		logging.error(f"Error: {e}")
		await interaction.response.send_message(f"Error: {e}", ephemeral=True)
	session.close()

@bot.tree.command(name="list_exception", description="List exception days")
@discord.app_commands.default_permissions(administrator=True)
async def list_exception(interaction: discord.Interaction):
	logging.debug(f"User {interaction.user} request list exception")
	session = Session()
	try:
		exceptions = ExceptionDay.get_all(session)
		await interaction.response.send_message(f"List of exception days: {', '.join([ datetime.strftime(exception.date, '%d/%m/%Y') for exception in exceptions ])}")
	except Exception as e:
		await interaction.response.send_message(f"Error: {e}", ephemeral=True)
	session.close()

if __name__ == "__main__":
	logging.info("Starting...")
	engine = create_engine(os.environ.get('ENGINE_URL'))
	Base.metadata.create_all(engine)
	Session = sessionmaker(bind=engine)
	bot.run(os.environ.get('DISCORD_TOKEN'))