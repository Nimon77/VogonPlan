import discord, logging

class Buttons(discord.ui.View):
	def __init__(self):
		super().__init__(timeout=None)

	@discord.ui.button(label="Lun. Matin", style=discord.ButtonStyle.blurple, emoji="1️⃣" , row=0, custom_id=f"lun_matin")
	async def button_lun_matin(self, interaction: discord.Interaction, button: discord.ui.Button):
		logging.debug(f"Interaction : {interaction}")
		logging.debug(f"Button : {button}")
		logging.debug(f"Self : {self}")
		await interaction.response.send_message(f"Button {button.label} clicked")

	@discord.ui.button(label="Lun. Après-midi", style=discord.ButtonStyle.blurple, emoji="1️⃣", row=0, custom_id=f"lun_apresmidi")
	async def button_lun_apresmidi(self, interaction: discord.Interaction, button: discord.ui.Button):
		await interaction.response.send_message(f"Button {button.label} clicked")

	@discord.ui.button(label="Mar. Matin", style=discord.ButtonStyle.blurple, emoji="2️⃣", row=1, custom_id=f"mar_matin")
	async def button_mar_matin(self, interaction: discord.Interaction, button: discord.ui.Button):
		await interaction.response.send_message(f"Button {button.label} clicked")

	@discord.ui.button(label="Mar. Après-midi", style=discord.ButtonStyle.blurple, emoji="2️⃣", row=1, custom_id=f"mar_apresmidi")
	async def button_mar_apresmidi(self, interaction: discord.Interaction, button: discord.ui.Button):
		await interaction.response.send_message(f"Button {button.label} clicked")

	@discord.ui.button(label="Mer. Matin", style=discord.ButtonStyle.blurple, emoji="3️⃣", row=2, custom_id=f"mer_matin")
	async def button_mer_matin(self, interaction: discord.Interaction, button: discord.ui.Button):
		await interaction.response.send_message(f"Button {button.label} clicked")

	@discord.ui.button(label="Mer. Après-midi", style=discord.ButtonStyle.blurple, emoji="3️⃣", row=2, custom_id=f"mer_apresmidi")
	async def button_mer_apresmidi(self, interaction: discord.Interaction, button: discord.ui.Button):
		await interaction.response.send_message(f"Button {button.label} clicked")

	@discord.ui.button(label="Jeu. Matin", style=discord.ButtonStyle.blurple, emoji="4️⃣", row=3, custom_id=f"jeu_matin")
	async def button_jeu_matin(self, interaction: discord.Interaction, button: discord.ui.Button):
		await interaction.response.send_message(f"Button {button.label} clicked")

	@discord.ui.button(label="Jeu. Après-midi", style=discord.ButtonStyle.blurple, emoji="4️⃣", row=3, custom_id=f"jeu_apresmidi")
	async def button_jeu_apresmidi(self, interaction: discord.Interaction, button: discord.ui.Button):
		await interaction.response.send_message(f"Button {button.label} clicked")

	@discord.ui.button(label="Ven. Matin", style=discord.ButtonStyle.blurple, emoji="5️⃣", row=4, custom_id=f"ven_matin")
	async def button_ven_matin(self, interaction: discord.Interaction, button: discord.ui.Button):
		await interaction.response.send_message(f"Button {button.label} clicked")

	@discord.ui.button(label="Ven. Après-midi", style=discord.ButtonStyle.blurple, emoji="5️⃣", row=4, custom_id=f"ven_apresmidi")
	async def button_ven_apresmidi(self, interaction: discord.Interaction, button: discord.ui.Button):
		await interaction.response.send_message(f"Button {button.label} clicked")