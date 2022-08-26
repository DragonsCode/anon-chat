from unicodedata import category
from sqlalchemy import Column, Integer

from models.model_admin import ModelAdmin
from models.database import Base


class Chats(Base, ModelAdmin):
    __tablename__ = "chats"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user = Column(Integer)
    interlocutor = Column(Integer)

    # required in order to acess columns with server defaults
    # or SQL expression defaults, subsequent to a flush, without
    # triggering an expired load
    #__mapper_args__ = {"eager_defaults": True}

    def __str__(self):
        return f'User: {self.user}\nInterlocutor: {self.interlocutor}'

    def __repr__(self):
        return (
            f"<{self.__class__.__name__}("
            f"user={self.user}, "
            f"interlocutor={self.interlocutor}"
            f")>"
        )
