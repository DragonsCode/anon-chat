from sqlalchemy import update
from sqlalchemy.future import select

from models.database import async_db_session


class ModelAdmin:
    @classmethod
    async def create(cls, **kwargs):
        async_db_session.add(cls(**kwargs))
        await async_db_session.commit()
    
    @classmethod
    async def delete(cls, user):
        user = await cls.get(user=user)
        await async_db_session.delete(user)
        await async_db_session.commit()
    
    @classmethod
    async def delete_channel(cls, channel):
        user = await cls.get_channel(channel=channel)
        await async_db_session.delete(user)
        await async_db_session.commit()
    
    @classmethod
    async def delete_bot(cls, bot):
        user = await cls.get_bot(bot=bot)
        await async_db_session.delete(user)
        await async_db_session.commit()

    @classmethod
    async def updater(cls, user, **kwargs):
        query = (
            update(cls)
            .where(cls.user == user)
            .values(**kwargs)
            .execution_options(synchronize_session="fetch")
        )

        await async_db_session.execute(query)
        await async_db_session.commit()

    @classmethod
    async def get(cls, user: int=0, interlocutor: int=0):
        query = None
        if user and interlocutor:
            query = select(cls).where(cls.user == user, interlocutor == interlocutor)
        elif user:
            query = select(cls).where(cls.user == user)
        elif interlocutor:
            query = select(cls).where(cls.interlocutor == interlocutor)
        else:
            query = select(cls)
        results = await async_db_session.execute(query)
        result = results.scalars().first()
        return result
    
    @classmethod
    async def get_channel(cls, channel: str):
        query = select(cls).where(cls.channel == channel)
        results = await async_db_session.execute(query)
        result = results.scalars().first()
        return result
    
    @classmethod
    async def get_bot(cls, bot: str):
        query = select(cls).where(cls.bot == bot)
        results = await async_db_session.execute(query)
        result = results.scalars().first()
        return result
    
    @classmethod
    async def get_all(cls):
        query = select(cls)
        results = None
        try:
            results = await async_db_session.execute(query)
        except:
            await async_db_session.rollback()
            results = await async_db_session.execute(query)
        result = results.scalars().all()
        return result