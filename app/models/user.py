import datetime, discord
from .base import Base
from sqlalchemy import Column, Integer, String, Boolean

class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True, autoincrement=True)
    discord_id = Column(String(255), nullable=False, unique=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    login = Column(String(100), nullable=False, unique=True)
    active = Column(Boolean, nullable=False, default=True)

    def __init__(self, discord_id, first_name, last_name, login):
        self.discord_id = discord_id
        self.first_name = first_name
        self.last_name = last_name
        self.login = login

    def __repr__(self):
        return f"<User {self.discord_id} {self.first_name} {self.last_name} {self.login} {self.active}>"

    def __str__(self):
        return f"{self.discord_id} {self.first_name} {self.last_name} {self.login} {self.active}"

    def to_dict(self):
        return {
            "id": self.id,
            "discord_id": self.discord_id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "login": self.login,
            "active": self.active
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
    def get_all_active(session):
        return session.query(User).filter_by(active=True).all()

    @staticmethod
    def get_all_partial(session, partial):
        return session.query(User).filter(User.login.like(f"%{partial}%")).all()

    @staticmethod
    def get_all_active_partial(session, partial):
        return session.query(User).filter_by(active=True).filter(User.login.like(f"%{partial}%")).all()

    @staticmethod
    def get_all_disabled_partial(session, partial):
        return session.query(User).filter_by(active=False).filter(User.login.like(f"%{partial}%")).all()

    @staticmethod
    def get_all_embed(session):
        embed = discord.Embed(
            title = "Liste des utilisateurs",
            description = "Liste des utilisateurs",
            color = 0x00ff00
        )
        for user in User.get_all_active(session):
            embed.add_field(
                name = f"{user.login}: {user.first_name} {user.last_name}",
                value = f"<@{user.discord_id}>",
                inline = False
            )
        return embed