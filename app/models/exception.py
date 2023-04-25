import datetime, discord

from .base import Base
from sqlalchemy import Column, Integer, Date

class ExceptionDay(Base):
    __tablename__ = 'exception_day'
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False, unique=True)

    def __init__(self, date):
        self.date = date

    def __repr__(self):
        return f"<ExceptionDay {self.date}>"

    def __str__(self):
        return f"{self.date}"

    def to_dict(self):
        return {
            "id": self.id,
            "date": self.date,
        }

    def to_json(self):
        return json.dumps(self.to_dict())

    def to_embed(self):
        embed = discord.Embed(
            title = f"Exception day {self.date}",
            color = 0x00ff00
        )
        return embed

    @staticmethod
    def get_by_date(session, date: datetime.date):
        return session.query(ExceptionDay).filter_by(date=datetime.datetime.strftime(date, '%Y-%m-%d')).first()

    @staticmethod
    def get_all(session):
        return session.query(ExceptionDay).all()

    @staticmethod
    def get_by_partial_date(session, partial_date):
        return session.query(ExceptionDay).filter(ExceptionDay.date.like(f"%{partial_date}%")).all()

    @staticmethod
    def get_all_as_list(session):
        return [exception_day.date for exception_day in session.query(ExceptionDay).all()]

    @staticmethod
    def get_by_partial_date_as_list(session, partial_date):
        return [exception_day.date for exception_day in session.query(ExceptionDay).filter(ExceptionDay.date.like(f"%{partial_date}%")).all()]

    @staticmethod
    def get_all_as_str(session):
        return ', '.join([exception_day.date for exception_day in session.query(ExceptionDay).all()])