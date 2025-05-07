from sqlalchemy import update
from sqlalchemy.future import select

from datetime import datetime

from models.database import async_db_session
from models.queue import Queue
from models.chats import Chats


class methods:
    async def get_user(chat: bool=False, user: int=0):
        if chat:
            user = await Chats.get(user=user)
            return user
        elif not chat:
            user = await Queue.get(user=user)
            return user
        else:
            user = await Queue.get()
            return user
    
    async def get_interlocutor(user: int=None, interlocutor: int=None):
        if user is not None and interlocutor is not None:
            user = await Chats.get(user=user, interlocutor=interlocutor)
            return user
        elif interlocutor:
            user = await Chats.get(interlocutor=interlocutor)
            return user
        else:
            return None
    
    async def count_queue():
        users = await Queue.get_all()
        return len(users)
    
    async def insert_queue(user: int):
        await Queue.create(user=user)
    
    async def insert_chat(user: int, interlocutor: int):
        await Chats.create(user=user, interlocutor=interlocutor)
    
    async def delete_queue(user: int):
        await Queue.delete(user=user)
    
    async def delete_chat(user: int):
        await Chats.delete(user=user)