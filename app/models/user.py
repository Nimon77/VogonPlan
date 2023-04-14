import datetime, discord
from .base import Base
from sqlalchemy import Column, Integer, String

class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    discord_id = Column(Integer, nullable=False)
    login = Column(String(100), nullable=False)

    def __init__(self, discord_id, login):
        self.discord_id = discord_id
        self.login = login

    def __repr__(self):
        return f"<User {self.discord_id} {self.login}>"

    def __str__(self):
        return f"{self.discord_id} {self.login}"

    def to_dict(self):
        return {
            "id": self.id,
            "discord_id": self.discord_id,
            "login": self.login
        }

    def to_json(self):
        return json.dumps(self.to_dict())

    def to_embed(self):
        embed = discord.Embed(
            title = f"User {self.login}",
            description = f"Discord id: {self.discord_id}",
            color = 0x00ff00
        )
        return embed

    @staticmethod
    def get_by_discord_id(session, discord_id):
        return session.query(User).filter_by(discord_id=discord_id).first()

    @staticmethod
    def get_by_id(session, id):
        return session.query(User).filter_by(id=id).first()

    @staticmethod
    def get_by_login(session, login):
        return session.query(User).filter_by(login=login).first()

    @staticmethod
    def get_all(session):
        return session.query(User).all()

    @staticmethod
    def get_all_embed(session):
        embed = discord.Embed(
            title = "Liste des utilisateurs",
            description = "Liste des utilisateurs",
            color = 0x00ff00
        )
        for user in User.get_all(session):
            embed.add_field(
                name = user.login,
                value = f"<@{user.discord_id}>",
                inline = False
            )
        return embed