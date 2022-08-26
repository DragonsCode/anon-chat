from sqlalchemy import Column, Integer, String

from models.model_admin import ModelAdmin
from models.database import Base


class Channels(Base, ModelAdmin):
    __tablename__ = "channel"
    id = Column(Integer, primary_key=True, autoincrement=True)
    link = Column(String(100))
    channel = Column(Integer)

    def __str__(self):
        return f'{self.channel}'

    def __repr__(self):
        return (
            f"<{self.__class__.__name__}("
            f"channel={self.channel}"
            f")>"
        )