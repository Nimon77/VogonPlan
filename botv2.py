import os, json, asyncio, discord, logging, coloredlogs, locale
from crontab import CronTab
from datetime import datetime, timedelta

coloredlogs.install(level='DEBUG')

locale.setlocale(locale.LC_ALL, 'fr_FR.UTF-8')

tasks = []

intents = discord.Intents.default()
intents.members = True

client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)

async def speak(interval, channel):
	try:
		await client.wait_until_ready()
		cron = CronTab(interval)
		logging.info(f"Starting cron job with interval {interval} for channel {channel}")
		while True:
			await asyncio.sleep(cron.next())
			try:
				now = datetime.now()
				lundi = now + timedelta(days=(-now.weekday())+7)
				try:
					with open('planning.json', 'r') as f:
						json_data = json.load(f)
				except:
					json_data = {}
				logging.debug(f"Sending message to {channel} <#{channel.id}> for week {lundi.strftime('%d/%m/%Y')}")
				await channel.send('<@&943868546079940678> le planning de presences de la semaine est arrivé !')
				for i in range(0,5):
					day = lundi + timedelta(days=i)
					embed=discord.Embed(title=day.strftime("%a %d %B %Y"))
					if json_data.get(day.strftime("%d/%m/%Y")) is not None:
						embed.add_field(name="Matin 1️⃣", value="\n".join(json_data.get(day.strftime("%d/%m/%Y"))["Matin"]), inline=True)
						embed.add_field(name="Après-midi 2️⃣", value="\n".join(json_data.get(day.strftime("%d/%m/%Y"))["Apres-midi"]), inline=True)
					else:
						embed.add_field(name="Matin 1️⃣", value="None", inline=True)
						embed.add_field(name="Après-midi 2️⃣", value="None", inline=True)
					msg = await channel.send(embed=embed)
					await msg.add_reaction('1️⃣')
					await msg.add_reaction('2️⃣')
					if json_data.get(day.strftime("%d/%m/%Y")) is None:
						json_data.update(
							{
								day.strftime("%d/%m/%Y"):
								{
									"Matin": ["None"],
									"Apres-midi": ["None"]
								}
							}
						)
				with open('planning.json', 'w') as f:
					json.dump(json_data, f)
			except:
				logging.error(f'I could not send Salut to `{channel}` :(')
	except asyncio.CancelledError:
		logging.info(f"Stopping cron job with interval {interval} for channel {channel}")


@client.event
async def on_ready():
	global tasks
	await tree.sync()
	# restart cron from file
	with open('cron.txt', 'r') as f:
		for line in f.readlines():
			if line != '':
				interval, channel_id = line.split('|')
				channel = client.get_channel(int(channel_id))
				tasks.append(client.loop.create_task(speak(interval, channel), name=f"{channel.id}"))
	logging.info(f'We have logged in as {client.user}')

@client.event
async def on_raw_reaction_add(payload):
	if not payload.member.bot and (payload.emoji.name == '1️⃣' or payload.emoji.name == '2️⃣'):
		channel = client.get_channel(payload.channel_id)
		message = await channel.fetch_message(payload.message_id)
		if (message.author == client.user):
			id = 0 if payload.emoji.name == '1️⃣' else 1
			msg = message.embeds[0]
			value = msg.fields[id].value.splitlines()
			if value[0] == "None":
				value = payload.member.display_name
			else:
				if payload.member.display_name not in value:
					value.append(payload.member.display_name)
				value = "\n".join(value)
			logging.debug(f"Added {payload.member.display_name} to {msg.fields[id].name}  for {msg.title}")
			msg.set_field_at(id, name=msg.fields[id].name, value=value)
			await message.edit(embed=msg)
			try:
				with open('planning.json', 'r') as f:
					data = json.load(f)
			except:
				data = {}
			date = datetime.strptime(msg.title, "%a %d %B %Y")
			data.update(
				{
					date.strftime("%d/%m/%Y"):
					{
						"Matin": msg.fields[0].value.splitlines(),
						"Apres-midi": msg.fields[1].value.splitlines()
					}
				}
			)
			with open('planning.json', 'w') as f:
				json.dump(data, f)



@client.event
async def on_raw_reaction_remove(payload):
	guild = client.get_guild(payload.guild_id)
	member = guild.get_member(payload.user_id)
	if member and not member.bot and (payload.emoji.name == '1️⃣' or payload.emoji.name == '2️⃣'):
		channel = client.get_channel(payload.channel_id)
		message = await channel.fetch_message(payload.message_id)
		if (message.author == client.user):
			id = 0 if payload.emoji.name == '1️⃣' else 1
			msg = message.embeds[0]
			value = msg.fields[id].value.splitlines()
			while not False:
				try:
					value.remove(member.display_name)
					logging.debug(f"Removed {member.display_name} from {msg.fields[id].name}  of {msg.title}")
				except:
					break
			if (not value): value = "None"
			else: value = "\n".join(value)
			msg.set_field_at(id, name=msg.fields[id].name, value=value)
			await message.edit(embed=msg);
			try:
				with open('planning.json', 'r') as f:
					data = json.load(f)
			except:
				data = {}
			date = datetime.strptime(msg.title, "%a %d %B %Y")
			data.update(
				{
					date.strftime("%d/%m/%Y"):
					{
						"Matin": msg.fields[0].value.splitlines(),
						"Apres-midi": msg.fields[1].value.splitlines()
					}
				}
			)
			with open('planning.json', 'w') as f:
				json.dump(data, f)

@tree.command(name = "planning", description = "Start planning cron in this channel")
async def planning(interaction: discord.Interaction, interval: str):
	global tasks
	logging.debug(f"User {interaction.user} request start planning cron in channel {interaction.channel} <#{interaction.channel_id}> with interval {interval}")
	if interaction.user.guild_permissions.administrator:
		logging.debug(f"Starting cron job in {interaction.channel_id}")
		logging.debug(f"Tasks : {[int(task.get_name()) for task in tasks]}")
		if interaction.channel.id not in [task.get_name() for task in tasks]:
			with open('cron.txt', 'a') as f:
				f.write(f'{interval}|{interaction.channel_id}\n')
			tasks.append(client.loop.create_task(speak(interval, interaction.channel), name=f'{interaction.channel_id}'))
			await interaction.response.send_message(f"Saving this channel for cron job `{interval}`")
		else:
			await interaction.response.send_message(f"This channel as already a cron job")
	else:
		await interaction.response.send_message(f"You need to be an administrator to use this command", ephemeral=True)

@tree.command(name = "stop", description = "Stop planned cron in this channel")
async def stop(interaction: discord.Interaction):
	global tasks
	logging.debug(f"User {interaction.user} request stop planning cron in channel {interaction.channel} <#{interaction.channel_id}>")
	if (interaction.user.guild_permissions.administrator):
		logging.debug(f"Stopping cron job in {interaction.channel_id}")
		logging.debug(f"Tasks : {[int(task.get_name()) for task in tasks]}")
		if (interaction.channel_id in [int(task.get_name()) for task in tasks]):
			# remove line from file
			with open('cron.txt', 'r') as f:
				lines = f.readlines()
			with open('cron.txt', 'w') as f:
				for line in lines:
					if int(line.split('|')[1]) != interaction.channel_id:
						f.write(line)
			# remove task
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

logging.info("Starting...")
client.run(os.environ.get('DISCORD_TOKEN'))