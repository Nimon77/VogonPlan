import os
import discord
import locale
import json
from datetime import datetime, timedelta

locale.setlocale(locale.LC_ALL, 'fr_FR.UTF-8')

intents = discord.Intents.default()
intents.members = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
	print('We have logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
	if message.author == client.user:
		return

	if message.content.startswith('$week') and message.author.guild_permissions.administrator:
		now = datetime.now()
		lundi = now + timedelta(days=(-now.weekday())+7)
		try:
			with open('planning.json', 'r') as f:
				json_data = json.load(f)
		except:
			json_data = {}
		for i in range(0,5):
			day = lundi + timedelta(days=i)
			embed=discord.Embed(title=day.strftime("%a %d %B %Y"))
			embed.add_field(name="Matin 1️⃣", value="None", inline=True)
			embed.add_field(name="Après-midi 2️⃣", value="None", inline=True)
			msg = await message.channel.send(embed=embed)
			await msg.add_reaction('1️⃣')
			await msg.add_reaction('2️⃣')
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
				value.append(payload.member.display_name)
				value = "\n".join(value)
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
	print(member.display_name)
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

# @client.event
# async def on_reaction_add(reaction, user):
# 	print("not raw")
# 	if reaction.message.author == client.user and user != client.user:
# 		if reaction.emoji == '1️⃣' or reaction.emoji == '2️⃣':
# 			id = 0 if reaction.emoji == '1️⃣' else 1
# 			msg = reaction.message.embeds[0]
# 			value = msg.fields[id].value.splitlines()
# 			if value[0] == "None":
# 				value = user.name
# 			else:
# 				value.append(user.name)
# 				value = "\n".join(value)
# 			msg.set_field_at(id, name=msg.fields[id].name, value=value)
# 			await reaction.message.edit(embed=msg)

# @client.event
# async def on_reaction_remove(reaction, user):
# 	print("not raw")
# 	if reaction.message.author == client.user and user != client.user:
# 		if reaction.emoji == '1️⃣' or reaction.emoji == '2️⃣':
# 			id = 0 if reaction.emoji == '1️⃣' else 1
# 			msg = reaction.message.embeds[0]
# 			value = msg.fields[id].value.splitlines()
# 			value.remove(user.name)
# 			if (not value): value = "None"
# 			else: value = "\n".join(value)
# 			msg.set_field_at(id, name=msg.fields[id].name, value=value)
# 			await reaction.message.edit(embed=msg);

print("Starting...")
client.run(os.environ.get('DISCORD_TOKEN'))
