# Table Planning (id, user_id, date, morning, afternoon)

# Path: app/models/Planning.py

import datetime, discord
from .base import Base
from sqlalchemy import Column, Integer, String, Date, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from .user import User

class Schedule(Base):
    __tablename__ = 'schedule'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    date = Column(Date, nullable=False)
    morning = Column(Boolean, nullable=False)
    afternoon = Column(Boolean, nullable=False)

    def __init__(self, user_id, date, morning, afternoon):
        self.user_id = user_id
        self.date = date
        self.morning = morning
        self.afternoon = afternoon

    def __repr__(self):
        return f"<Schedule {self.user_id} {self.date} {self.morning} {self.afternoon}>"

    def __str__(self):
        return f"{self.user_id} {self.date} {self.morning} {self.afternoon}"

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "date": self.date,
            "morning": self.morning,
            "afternoon": self.afternoon
        }

    def to_json(self):
        return json.dumps(self.to_dict())

    def to_embed(self):
        embed = discord.Embed(
            title = f"Schedule du {self.date.strftime('%d/%m/%Y')}",
            description = f"Schedule de {self.user}",
            color = 0x00ff00
        )
        
        embed.add_field(
            name = "Matin",
            value = "None" if not self.morning else self.user.login,
            inline = False
        )
        embed.add_field(
            name = "Apres-midi",
            value = "None" if not self.afternoon else self.user.login,
            inline = False
        )
        return embed

    @staticmethod
    def get_by_date(session, date):
        return session.query(Schedule).filter_by(date=date).all()

    @staticmethod
    def get_by_user_id(session, user_id):
        return session.query(Schedule).filter_by(user_id=user_id).all()

    @staticmethod
    def get_by_user_id_and_date(session, user_id, date):
        return session.query(Schedule).filter_by(user_id=user_id, date=date).first()

    @staticmethod
    def get_by_date_range(session, start_date, end_date):
        return session.query(Schedule).filter(Schedule.date >= start_date, Schedule.date <= end_date).all()