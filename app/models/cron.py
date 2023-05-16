# Table cron (id, cron, channel_id)
# Path: app/models/cron.py

import datetime, discord
from .base import Base
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

class Cron(Base):
    __tablename__ = 'cron'
    id = Column(Integer, primary_key=True)
    channel_id = Column(String(20), nullable=False, unique=True)
    interval = Column(String(100), nullable=False)

    def __init__(self, channel_id, interval):
        self.channel_id = channel_id
        self.interval = interval

    def __repr__(self):
        return f"<Cron {self.channel_id} {self.interval}>"

    def __str__(self):
        return f"{self.channel_id} {self.interval}"

    def to_dict(self):
        return {
            "id": self.id,
            "channel_id": self.channel_id,
            "interval": self.interval
        }

    def to_json(self):
        return json.dumps(self.to_dict())

    def to_embed(self):
        embed = discord.Embed(
            title = f"Interval {self.interval}",
            description = f"Channel id: {self.channel_id}",
            color = 0x00ff00
        )
        return embed

    @staticmethod
    def get_all(session):
        return session.query(Cron).all()

    @staticmethod
    def get_by_channel_id(session, channel_id):
        return session.query(Cron).filter_by(channel_id=channel_id).first()

    @staticmethod
    def get_all_embed(session):
        embed = discord.Embed(
            title = "Liste des intervalles",
            description = "Liste des intervalles",
            color = 0x00ff00
        )
        for cron in Cron.get_all(session):
            embed.add_field(name=f"Channel id: <#{cron.channel_id}>", value=f"Interval: `{cron.interval}`", inline=False)
        return embed