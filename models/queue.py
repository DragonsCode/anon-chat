from sqlalchemy import Column, Integer

from models.model_admin import ModelAdmin
from models.database import Base


class Queue(Base, ModelAdmin):
    def __init__(self, user: int):
        self.user = user
        super(Queue, self).__init__()
    __tablename__ = "queue"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user = Column(Integer)

    def __str__(self):
        return f'{self.user}'

    def __repr__(self):
        return (
            f"<{self.__class__.__name__}("
            f"user={self.user}"
            f")>"
        )