import asyncio
import json
import locale
import logging
import os
import signal
from datetime import datetime, timedelta

import coloredlogs
import discord
import requests
from crontab import CronTab
from discord.ext import commands
from dotenv import load_dotenv
from models.base import Base
from models.cron import Cron
from models.exception import ExceptionDay
from models.schedule import Schedule
from models.user import User
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

load_dotenv()

if os.getenv("DEBUG") == "True":
    coloredlogs.install(level='DEBUG')
else:
    coloredlogs.install(level='INFO')

locale.setlocale(locale.LC_ALL, 'fr_FR.UTF-8')

tasks = []

class GracefulKiller:
    def __init__(self):
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, signum, frame):
        logging.warning('gracefully exitting')
        bot.loop.stop()
        exit(0)

# -------------------------------- Bot Setup --------------------------------

class PesistentBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True

        super().__init__(intents=intents, command_prefix="JeSuisDisabled", case_insensitive=True)

    async def setup_hook(self):
        self.add_view(SingleButton())

    async def on_ready(self):
        global tasks
        await self.tree.sync()
        # restart cron from file
        logging.info(f'We have logged in as {self.user}')
        session = Session()
        crons = Cron.get_all(session)
        if len(crons) > 0:
            logging.info(f"Restarting {len(crons)} cron jobs")
        else:
            logging.info(f"No cron job to restart")
        for cron in crons:
            channel = self.get_channel(int(cron.channel_id))
            if f"{channel.id}" in [task.get_name() for task in tasks]:
                logging.info(msg=f"Cron job with interval `{cron.interval}` for channel `{channel}` on server `{channel.guild}` already running")
                continue
            logging.info(msg=f"Restarting cron job with interval `{cron.interval}` for channel `{channel}` on server `{channel.guild}`")
            tasks.append(self.loop.create_task(auto_schedule(cron.interval, channel), name=f"{channel.id}"))
        session.close()

bot = PesistentBot()

# --------------------------------- Commands ---------------------------------

# ------------------ Schedule management ------------------

@bot.tree.command(name = "start_schedule", description = "Start schedule cron in this channel")
@discord.app_commands.default_permissions(administrator=True)
async def start_schedule(interaction: discord.Interaction, interval: str):
    global tasks
    logging.debug(f"User {interaction.user} request start schedule cron in channel `{interaction.channel}` with interval `{interval}` on server `{interaction.guild}`")
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

@bot.tree.command(name = "list_schedules", description = "List all planned cron")
@discord.app_commands.default_permissions(administrator=True)
async def list_schedules(interaction: discord.Interaction):
    logging.debug(f"User {interaction.user} request list planned cron on server `{interaction.guild}`")
    session = Session()
    if len(session.query(Cron).all()) > 0:
        await interaction.response.send_message(embed=Cron.get_all_embed(session), ephemeral=True)
    else:
        await interaction.response.send_message(f"No planned cron", ephemeral=True)


@bot.tree.command(name = "stop_schedule", description = "Stop planned cron in this channel")
@discord.app_commands.default_permissions(administrator=True)
async def stop_schedule(interaction: discord.Interaction):
    global tasks
    logging.info(f"User {interaction.user} request stop planning cron in channel {interaction.channel} <#{interaction.channel_id}>")
    logging.debug(f"Tasks : {[task.get_name() for task in tasks]}")
    if (str(interaction.channel_id) in [task.get_name() for task in tasks]):
        logging.debug(f"Stopping cron job in {interaction.channel_id}")
        session = Session()
        session.delete(Cron.get_by_channel_id(session, str(interaction.channel_id)))
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

# ------------------ Cron job ------------------
def number_to_emoji(number):
    return [ "0️⃣", "1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟" ][number]

class SingleButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Toggle", style=discord.ButtonStyle.green, custom_id="toggle")
    async def toggle(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        session = Session()
        date = datetime.strptime(interaction.message.embeds[0].title, "%a %d %B %Y")
        user = User.get_by_discord_id(session, str(interaction.user.id))
        if not user:
            session.add(User(discord_id=str(interaction.user.id), login=interaction.user.name))
            session.commit()
            user = User.get_by_discord_id(session, str(interaction.user.id))
        Schedule.switch_registered(session, user.id, date)
        schedules = [ schedule for schedule in Schedule.get_by_date(session, date) if schedule.registered ]
        logging.debug("List Schedules: %s", schedules)
        edited_embed = interaction.message.embeds[0]
        edited_embed.set_field_at(0, name="Matin", value="\n".join([ f"{number_to_emoji(i+1)} {schedule.user.login}" for i, schedule in enumerate(schedules) ]))
        await interaction.message.edit(embed=edited_embed)
        session.close()

    @discord.ui.button(emoji="🔄", style=discord.ButtonStyle.blurple, custom_id="reload")
    async def reload(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        session = Session()
        date = datetime.strptime(interaction.message.embeds[0].title, "%a %d %B %Y")
        schedules = [ schedule for schedule in Schedule.get_by_date(session, date) if schedule.registered ]
        logging.debug(f"List Schedules: {schedules}")
        edited_embed = interaction.message.embeds[0]
        edited_embed.set_field_at(0, name="Qui ?", value="\n".join([ f"{number_to_emoji(i+1)} {schedule.user.login}" for i, schedule in enumerate(schedules) ]))
        await interaction.message.edit(embed=edited_embed)
        session.close()

async def send_schedule(channel, lundi):
    try:
        embeds = []
        session = Session()
        JoursFeries = requests.get("https://calendrier.api.gouv.fr/jours-feries/metropole/" + str(lundi.year) + ".json").json()
        for i in range(0, 5):
            date = lundi + timedelta(days=i)
            schedules = [ schedule for schedule in Schedule.get_by_date(session, date) if schedule.registered ]
            # Color gradient
            bank = date.strftime("%Y-%m-%d") in JoursFeries
            bankName = JoursFeries[date.strftime("%Y-%m-%d")] if bank else None
            exceptionDay = False
            if not bank:
                exceptionDay = ExceptionDay.get_by_date(session, date) is not None
            logging.debug("Day: %s Bank: %s Exception: %s", date, bank, exceptionDay)
            embed = discord.Embed(title=date.strftime("%a %d %B %Y"), color=[0x00FFFF, 0xFF0000][bank|exceptionDay])
            if not bank and not exceptionDay:
                embed.add_field(name="Qui ?", value="\n".join([ f"{number_to_emoji(i+1)} {schedule.user.login}" for i, schedule in enumerate(schedules) ]))
            if bank:
                embed.set_footer(text="Jour férié : " + bankName)
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
            await channel.send(f"<a:dancing_duck:1105889736486297602> Hello <@&1346134847734808689>! The schedule for week {(now + timedelta(days=(-now.weekday())+7)).isocalendar().week} is ready! <a:dancing_duck:1105889736486297602>")
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

@bot.tree.command(name="remove_exception", description="Remove an exception day")
@discord.app_commands.default_permissions(administrator=True)
@discord.app_commands.autocomplete(date=date_list_auto_complete)
@discord.app_commands.describe(date="Date of the exception day (DD/MM/YYYY)")
async def remove_exception(interaction: discord.Interaction, date: str):
    logging.info(f"User {interaction.user} request remove exception")
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
                planning_dict[schedule.date] = {"day": []}
            if schedule.registered:
                planning_dict[schedule.date]["day"].append(schedule.user)
            if schedule.user not in users:
                users.append(schedule.user)
        planning_dict = dict(sorted(planning_dict.items()))
        logging.debug(f"Planning dict: {planning_dict}")

        # Create the CSV file
        with open("planning.csv", "w") as file:
            file.write("Date;day;")
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
                    if user in planning_dict[date]["day"]:
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
    GracefulKiller()
    logging.info("Starting...")
    engine = create_engine(os.environ.get('ENGINE_URL'))
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    bot.run(os.environ.get('DISCORD_TOKEN'))

