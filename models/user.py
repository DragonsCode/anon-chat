from sqlalchemy import Column, Integer

from models.model_admin import ModelAdmin
from models.database import Base


class Users(Base, ModelAdmin):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user = Column(Integer)
    referals = Column(Integer, default=0)

    def __str__(self):
        return f'{self.user}'

    def __repr__(self):
        return (
            f"<{self.__class__.__name__}("
            f"user={self.user}"
            f")>"
        )