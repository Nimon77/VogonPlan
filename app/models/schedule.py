# Table Planning (id, user_id, date, morning, afternoon)

# Path: app/models/Planning.py

import datetime, discord, logging, json
from .base import Base
from sqlalchemy import Column, Integer, String, Date, Boolean, ForeignKey
from sqlalchemy.orm import relationship, backref
from .user import User

class Schedule(Base):
    __tablename__ = 'schedule'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    date = Column(Date, nullable=False)
    registered = Column(Boolean, nullable=False, default=False)
    user = relationship("User", backref=backref("schedule", cascade="all, delete-orphan"))

    def __init__(self, user_id, date, registered):
        self.user_id = user_id
        self.date = date
        self.registered = registered

    def __repr__(self):
        return f"<Schedule {self.user_id} {self.date} {self.registered}>"

    def __str__(self):
        return f"{self.user_id} {self.date} {self.registered}"

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "date": self.date,
            "registered": self.registered,
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
            name = "Qui ?",
            value = "None" if not self.registered else self.user.login,
            inline = False
        )
        return embed

    @staticmethod
    def get_by_date(session, date):
        return session.query(Schedule).filter_by(date=datetime.datetime.strftime(date, '%Y-%m-%d')).all()

    @staticmethod
    def get_by_user_id(session, user_id):
        return session.query(Schedule).filter_by(user_id=user_id).all()

    @staticmethod
    def get_by_user_id_and_date(session, user_id, date):
        return session.query(Schedule).filter_by(user_id=user_id, date=datetime.datetime.strftime(date, '%Y-%m-%d')).first()

    @staticmethod
    def get_by_date_range(session, start_date, end_date):
        return session.query(Schedule).filter(Schedule.date >= start_date, Schedule.date <= end_date).all()

    @staticmethod
    def switch_registered(session, user_id, date):
        logging.debug("switch_registered")
        schedule = Schedule.get_by_user_id_and_date(session, user_id, date)
        if schedule:
            schedule.registered = not schedule.registered
        else:
            schedule = Schedule(user_id, date, True)
            session.add(schedule)
        session.commit()
        return schedule
