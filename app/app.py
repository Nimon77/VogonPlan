import os, json, asyncio, discord, logging, coloredlogs, locale

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from crontab import CronTab
from datetime import datetime, timedelta

from models.base import Base
from models.cron import Cron
from models.user import User
from models.schedule import Schedule

coloredlogs.install(level='DEBUG')

locale.setlocale(locale.LC_ALL, 'fr_FR.UTF-8')

tasks = []

intents = discord.Intents.default()
intents.members = True

client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)

# async def send_schedule(interval, channel):
# 	try:
# 		await client.wait_until_ready()
# 		cron = CronTab(interval)
# 		logging.info(f"Starting cron job with interval `{interval}` for channel `{channel}` on `{channel.guild}`")
# 		while True:
# 			await asyncio.sleep(cron.next(default_utc=True))
# 			try:
# 				now = datetime.now()
# 				lundi = now + timedelta(days=(-now.weekday())+7)
# 				try:
# 					with open('planning.json', 'r') as f:
# 						json_data = json.load(f)
# 				except:
# 					json_data = {}
# 				logging.debug(f"Sending message to {channel} on server {channel.guild} for week {lundi.strftime('%d/%m/%Y')}")
# 				await channel.send('<@&943868546079940678> le planning de presences de la semaine est arrivé !')
# 				for i in range(0,5):
# 					day = lundi + timedelta(days=i)
# 					embed=discord.Embed(title=day.strftime("%a %d %B %Y"))
# 					if json_data.get(day.strftime("%d/%m/%Y")) is not None:
# 						embed.add_field(name="Matin 1️⃣", value="\n".join(json_data.get(day.strftime("%d/%m/%Y"))["Matin"]), inline=True)
# 						embed.add_field(name="Après-midi 2️⃣", value="\n".join(json_data.get(day.strftime("%d/%m/%Y"))["Apres-midi"]), inline=True)
# 					else:
# 						embed.add_field(name="Matin 1️⃣", value="None", inline=True)
# 						embed.add_field(name="Après-midi 2️⃣", value="None", inline=True)
# 					msg = await channel.send(embed=embed)
# 					await msg.add_reaction('1️⃣')
# 					await msg.add_reaction('2️⃣')
# 					if json_data.get(day.strftime("%d/%m/%Y")) is None:
# 						json_data.update(
# 							{
# 								day.strftime("%d/%m/%Y"):
# 								{
# 									"Matin": ["None"],
# 									"Apres-midi": ["None"]
# 								}
# 							}
# 						)
# 				with open('planning.json', 'w') as f:
# 					json.dump(json_data, f)
# 			except:
# 				logging.error(f'I could not send Salut to `{channel}` :(')
# 	except asyncio.CancelledError:
# 		logging.info(f"Stopping cron job with interval `{interval}` for channel `{channel}` on server `{channel.guild}`")

@client.event
async def on_ready():
	global tasks
	await tree.sync()
	# restart cron from file
	session = Session()
	crons = Cron.get_all(session)
	for cron in crons:
		channel = client.get_channel(cron.channel_id)
		logging.debug(msg=f"Restarting cron job with interval `{cron.interval}` for channel `{cron.channel_id}` on server `{channel.guild}`")
		tasks.append(client.loop.create_task(send_schedule(cron.interval, channel), name=f"{channel.id}"))
	logging.info(f'We have logged in as {client.user}')

# @client.event
# async def on_raw_reaction_add(payload):
# 	if not payload.member.bot and (payload.emoji.name == '1️⃣' or payload.emoji.name == '2️⃣'):
# 		channel = client.get_channel(payload.channel_id)
# 		message = await channel.fetch_message(payload.message_id)
# 		if (message.author == client.user):
# 			id = 0 if payload.emoji.name == '1️⃣' else 1
# 			msg = message.embeds[0]
# 			value = msg.fields[id].value.splitlines()
# 			if value[0] == "None":
# 				value = payload.member.display_name
# 			else:
# 				if payload.member.display_name not in value:
# 					value.append(payload.member.display_name)
# 				value = "\n".join(value)
# 			logging.debug(f"Added {payload.member.display_name} to {msg.fields[id].name}  for {msg.title}")
# 			msg.set_field_at(id, name=msg.fields[id].name, value=value)
# 			await message.edit(embed=msg)
# 			try:
# 				with open('planning.json', 'r') as f:
# 					data = json.load(f)
# 			except:
# 				data = {}
# 			date = datetime.strptime(msg.title, "%a %d %B %Y")
# 			data.update(
# 				{
# 					date.strftime("%d/%m/%Y"):
# 					{
# 						"Matin": msg.fields[0].value.splitlines(),
# 						"Apres-midi": msg.fields[1].value.splitlines()
# 					}
# 				}
# 			)
# 			with open('planning.json', 'w') as f:
# 				json.dump(data, f)

# @client.event
# async def on_raw_reaction_remove(payload):
# 	guild = client.get_guild(payload.guild_id)
# 	member = guild.get_member(payload.user_id)
# 	if member and not member.bot and (payload.emoji.name == '1️⃣' or payload.emoji.name == '2️⃣'):
# 		channel = client.get_channel(payload.channel_id)
# 		message = await channel.fetch_message(payload.message_id)
# 		if (message.author == client.user):
# 			id = 0 if payload.emoji.name == '1️⃣' else 1
# 			msg = message.embeds[0]
# 			value = msg.fields[id].value.splitlines()
# 			while not False:
# 				try:
# 					value.remove(member.display_name)
# 					logging.debug(f"Removed {member.display_name} from {msg.fields[id].name}  of {msg.title}")
# 				except:
# 					break
# 			if (not value): value = "None"
# 			else: value = "\n".join(value)
# 			msg.set_field_at(id, name=msg.fields[id].name, value=value)
# 			await message.edit(embed=msg);
# 			try:
# 				with open('planning.json', 'r') as f:
# 					data = json.load(f)
# 			except:
# 				data = {}
# 			date = datetime.strptime(msg.title, "%a %d %B %Y")
# 			data.update(
# 				{
# 					date.strftime("%d/%m/%Y"):
# 					{
# 						"Matin": msg.fields[0].value.splitlines(),
# 						"Apres-midi": msg.fields[1].value.splitlines()
# 					}
# 				}
# 			)
# 			with open('planning.json', 'w') as f:
# 				json.dump(data, f)

# --------------------------------- Commands ---------------------------------

# ------------------ Schedule management ------------------

@tree.command(name = "start_schedule", description = "Start schedule cron in this channel")
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
				tasks.append(client.loop.create_task(send_schedule(interval, interaction.channel), name=f'{interaction.channel_id}'))
				await interaction.response.send_message(f"Saving this channel for cron job `{interval}`")
			except Exception as e:
				logging.error(f"Error while adding cron job to database : {e}")
		else:
			await interaction.response.send_message(f"This channel as already a cron job")
	else:
		await interaction.response.send_message(f"You need to be an administrator to use this command", ephemeral=True)

@tree.command(name = "list_schedules", description = "List all planned cron")
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


@tree.command(name = "stop_schedule", description = "Stop planned cron in this channel")
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


# ------------------ User management ------------------

@tree.command(name="add_user", description="Add a new user")
@discord.app_commands.default_permissions(administrator=True)
async def add_user(interaction: discord.Interaction, login: str, discord_user: discord.Member):
	logging.debug(f"User {interaction.user} request add user {login} with discord id {discord_user.id}")
	if (interaction.user.guild_permissions.administrator):
		session = Session()
		session.add(User(login=login, discord_id=discord_user.id))
		session.commit()
		session.close()
		await interaction.response.send_message(f"User `{login}` added with discord id <@{discord_user.id}>")
	else:
		await interaction.response.send_message(f"You are not an administrator", ephemeral=True)

@tree.command(name="remove_user", description="Remove a user")
@discord.app_commands.default_permissions(administrator=True)
async def remove_user(interaction: discord.Interaction, login: str):
	logging.debug(f"User {interaction.user} request remove user {login}")
	if (interaction.user.guild_permissions.administrator):
		session = Session()
		user = User.get_by_login(session, login)
		if user:
			session.delete(user)
			session.commit()
		session.close()
		await interaction.response.send_message(f"User `{login}` removed")
	else:
		await interaction.response.send_message(f"You are not an administrator", ephemeral=True)

@tree.command(name="rename_user", description="Rename a user")
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

@tree.command(name="list_users", description="List all users")
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

class Buttons(discord.ui.View):
	def __init__(self):
		super().__init__()

	@discord.ui.button(label="Lun. Matin", style=discord.ButtonStyle.blurple, emoji="1️⃣" , row=0)
	async def button_lun_matin(self, button: discord.ui.Button, interaction: discord.Interaction):
		await interaction.response.send_message(f"Button {button.label} clicked")

	@discord.ui.button(label="Lun. Après-midi", style=discord.ButtonStyle.blurple, emoji="1️⃣", row=0)
	async def button_lun_apresmidi(self, button: discord.ui.Button, interaction: discord.Interaction):
		await interaction.response.send_message(f"Button {button.label} clicked")

	@discord.ui.button(label="Mar. Matin", style=discord.ButtonStyle.blurple, emoji="2️⃣", row=1)
	async def button_mar_matin(self, button: discord.ui.Button, interaction: discord.Interaction):
		await interaction.response.send_message(f"Button {button.label} clicked")

	@discord.ui.button(label="Mar. Après-midi", style=discord.ButtonStyle.blurple, emoji="2️⃣", row=1)
	async def button_mar_apresmidi(self, button: discord.ui.Button, interaction: discord.Interaction):
		await interaction.response.send_message(f"Button {button.label} clicked")

	@discord.ui.button(label="Mer. Matin", style=discord.ButtonStyle.blurple, emoji="3️⃣", row=2)
	async def button_mer_matin(self, button: discord.ui.Button, interaction: discord.Interaction):
		await interaction.response.send_message(f"Button {button.label} clicked")

	@discord.ui.button(label="Mer. Après-midi", style=discord.ButtonStyle.blurple, emoji="3️⃣", row=2)
	async def button_mer_apresmidi(self, button: discord.ui.Button, interaction: discord.Interaction):
		await interaction.response.send_message(f"Button {button.label} clicked")

	@discord.ui.button(label="Jeu. Matin", style=discord.ButtonStyle.blurple, emoji="4️⃣", row=3)
	async def button_jeu_matin(self, button: discord.ui.Button, interaction: discord.Interaction):
		await interaction.response.send_message(f"Button {button.label} clicked")

	@discord.ui.button(label="Jeu. Après-midi", style=discord.ButtonStyle.blurple, emoji="4️⃣", row=3)
	async def button_jeu_apresmidi(self, button: discord.ui.Button, interaction: discord.Interaction):
		await interaction.response.send_message(f"Button {button.label} clicked")

	@discord.ui.button(label="Ven. Matin", style=discord.ButtonStyle.blurple, emoji="5️⃣", row=4)
	async def button_ven_matin(self, button: discord.ui.Button, interaction: discord.Interaction):
		await interaction.response.send_message(f"Button {button.label} clicked")

	@discord.ui.button(label="Ven. Après-midi", style=discord.ButtonStyle.blurple, emoji="5️⃣", row=4)
	async def button_ven_apresmidi(self, button: discord.ui.Button, interaction: discord.Interaction):
		await interaction.response.send_message(f"Button {button.label} clicked")


@tree.command(name="test", description="Test command")
async def test(interaction: discord.Interaction):
	now = datetime.now()
	lundi = now + timedelta(days=(-now.weekday())+7)

	embed = discord.Embed(title="Test", color=0x00FFFF)
	for i in range(0, 5):
		day = lundi + timedelta(days=i)
		embed.add_field(name=day.strftime("%a %d %B %Y"), value="", inline=False)
		embed.add_field(name="Matin", value="toto", inline=True)
		embed.add_field(name="Après-midi", value="tata", inline=True)
	
	await interaction.response.send_message(embed=embed, view=Buttons())


if __name__ == "__main__":
	logging.info("Starting...")
	# engine = create_engine('postgresql://benevoles:toto42@postgres/postgres')
	engine = create_engine('sqlite:///planning.db')
	Base.metadata.create_all(engine)
	Session = sessionmaker(bind=engine)
	client.run(os.environ.get('DISCORD_TOKEN'))