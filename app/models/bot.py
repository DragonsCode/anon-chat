from sqlalchemy import Column, Integer, String

from models.model_admin import ModelAdmin
from models.database import Base


class Bots(Base, ModelAdmin):
    __tablename__ = "bot"
    id = Column(Integer, primary_key=True, autoincrement=True)
    bot = Column(String(100))


    def __str__(self):
        return f'{self.bot}'

    def __repr__(self):
        return (
            f"<{self.__class__.__name__}("
            f"bot={self.bot}"
            f")>"
        )