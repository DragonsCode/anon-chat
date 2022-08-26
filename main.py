from aiogram import Bot, Dispatcher, types, executor
from aiogram.dispatcher.filters import IDFilter
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

from models.db_api import methods as db
from models.database import async_db_session
from models.bot import Bots
from models.channel import Channels
from models.user import Users

import logging

import asyncio

menus = ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton('Начать поиск'))

dating = ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton('Продолжить поиск')).add(KeyboardButton('Покинуть чат'))

searching = ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton('Остановить поиск'))


ADMIN = [235519518, 5161665132]

logging.basicConfig(level=logging.INFO)
bot = Bot(token="1682322424:AAE30aCB0ZY7hH6P7-CtKqGBay34ZN9mPiY")
dp = Dispatcher(bot)


@dp.message_handler(IDFilter(chat_id=ADMIN), commands="pub")
async def pub(message: types.Message):
    msg = message.text[4:]
    if len(msg) < 5:
        await message.answer('Слишком короткий')
        return
    users = await Users.get_all()
    for i in users:
        await bot.send_message(i.user, msg)
        await asyncio.sleep(0.4)
    await message.answer("Успешно отправлено")


@dp.message_handler(IDFilter(chat_id=ADMIN), commands="bot")
async def add_bot(message: types.Message):
    msg = message.text.split(' ')
    if len(msg) < 2:
        await message.answer('Используйте эту команду правильно: /bot token')
        return
    await Bots.create(bot=msg[1])
    await message.answer("Успешно создана")


@dp.message_handler(IDFilter(chat_id=ADMIN), commands="channel")
async def add_channel(message: types.Message):
    msg = message.text.split(' ')
    if len(msg) < 2 or msg[1][0] != '@':
        await message.answer('Используйте эту команду правильно: /channel @channel')
        return
    await Channels.create(channel=msg[1])
    await message.answer("Успешно создана")


@dp.message_handler(IDFilter(chat_id=ADMIN), commands="bots")
async def all_bots(message: types.Message):
    text = 'Вот токены ботов:\n'
    bots = await Bots.get_all()
    for i in bots:
        text += i.bot+'\n'
    await message.answer(text)


@dp.message_handler(IDFilter(chat_id=ADMIN), commands="channels")
async def all_channels(message: types.Message):
    text = 'Вот каналы:\n'
    channels = await Channels.get_all()
    for i in channels:
        text += i.channel+'\n'
    await message.answer(text)

@dp.message_handler(IDFilter(chat_id=ADMIN), commands="del_bot")
async def delete_bot(message: types.Message):
    msg = message.text.split(' ')
    if len(msg) < 2:
        await message.answer("Используйте эту команду правильно: /del_bot token")
        return
    channel = await Bots.get_bot(bot=msg[1])
    if channel is None:
        await message.answer("Токен не найден")
        return
    await Bots.delete_bot(bot=msg[1])
    await message.answer("Успешно удалено")


@dp.message_handler(IDFilter(chat_id=ADMIN), commands="del_channel")
async def delete_channel(message: types.Message):
    msg = message.text.split(' ')
    if len(msg) < 2 or msg[1][0] != '@':
        await message.answer("Используйте эту команду правильно: /del_channel @channel")
        return
    channel = await Channels.get_channel(channel=msg[1])
    if channel is None:
        await message.answer("Канал не найден")
        return
    await Channels.delete_channel(channel=msg[1])
    await message.answer("Успешно удалено")

@dp.message_handler(commands="start")
async def menu(message: types.Message):
    user = await Users.get(user=message.from_user.id)
    print(user)
    if user is None:
        await Users.create(user=message.from_user.id)
    await message.answer("🫂Для поиска собеседника напишите /search, или используйте кнопки", reply_markup=menus)

 
@dp.message_handler(commands="search")
@dp.message_handler(text='Начать поиск')
async def search_user_act(message: types.Message):
    bots = await Bots.get_all()
    channels = await Channels.get_all()
    to_sub = []
    to_start = []

    for i in bots:
        bot2 = Bot(token=i.bot)
        try:
            await bot2.send_chat_action(message.from_user.id, 'typing')
            #await bot2.session.close()
        except Exception as e:
            print(e)
            username = (await bot2.get_me()).username
            to_start.append('@'+username)
        sess = await bot2.get_session()
        await sess.close()
    
    for i in channels:
        user = await bot.get_chat_member(i.channel, message.from_user.id)
        if user.status == 'left' or user.status == 'banned':
            to_sub.append(i.channel)
    
    if len(to_sub) > 0 or len(to_start) > 0:
        text = ''
        
        if len(to_sub) > 0:
            text += 'Вы должны подписаться на некоторые каналы:\n'
            for i in to_sub:
                text += i+'\n'
        
        if len(to_start) > 0:
            text += 'Вы должны запустить несколько ботов:\n'
            for i in to_start:
                text += i+'\n'
        
        await message.answer(text)
        return
    if message.chat.type == "private":
        chatting = await db.get_user(chat=True, user=message.from_user.id)
        print(chatting)
        if chatting is not None:
            await message.answer("🧐Вы уже находитесь в чате с другим пользователем\n\n💡Для начала стоит прекратить текущий диалог")
        else:
            in_queue = await db.get_user(user=message.from_user.id)
            print(in_queue)
            if in_queue is None:
                interlocutor = await db.get_user()

                if interlocutor is None:
                    await db.insert_queue(user=message.from_user.id)
                    await message.answer("🔍Начал искать вам подходящего собеседника, подождите... \n\n💡Вы можете закончить поиск написав /stop_search, или нажав кнопку", reply_markup=searching)
                else:
                    queues = await db.count_queue()
                    print(queues)
                    if queues != 0:
                        try:
                            await db.delete_queue(user=message.from_user.id)
                        except Exception as e:
                            print(e)
                        try:
                            await db.delete_queue(user=interlocutor.user)
                        except Exception as e:
                            print(e)

                        await db.insert_chat(user=message.from_user.id, interlocutor=interlocutor.user)
                        await db.insert_chat(user=interlocutor.user, interlocutor=message.from_user.id)


                        chat_info = await db.get_interlocutor(user=message.from_user.id, interlocutor=interlocutor.user)

                        await message.answer(f"Собеседник найден! Вы можете начать общаться.", reply_markup=dating)
                        await bot.send_message(text=f"Собеседник найден! Вы можете начать общаться.", chat_id=chat_info.interlocutor, reply_markup=dating)
                    else:
                        await db.insert_queue(user=message.from_user.id)
                        await message.answer("🔍Начал искать вам подходящего собеседника, подождите... \n\n💡Вы можете закончить поиск написав /stop_search, или нажав кнопку", reply_markup=searching)

            else:
                await message.answer("🧐Вы уже находитесь в поиске\n\n💡Как только появится собеседник – я вас свяжу")
 
@dp.message_handler(commands="stop_search")
@dp.message_handler(text='Остановить поиск')
async def stop_search_act(message: types.Message):
    user = await db.get_user(user=message.from_user.id)
    print(user)
    if user is not None:
        await db.delete_queue(user=message.from_user.id)
        await menu(message)
    else:
        await message.answer("❌Вы еще не начали поиск, чтобы его закончить")

@dp.message_handler(commands="next")
@dp.message_handler(text='Продолжить поиск')
async def next(message: types.Message):
    user = await db.get_user(chat=True, user=message.from_user.id)
    print(user)
    if user is not None:
        await db.delete_chat(user=message.from_user.id)
        await db.delete_chat(user=user.interlocutor)
        await bot.send_message(text="😔Пользователь решил покинуть диалог...\n\n💡Продолжим поиск нового собеседника?", chat_id=user.interlocutor, reply_markup=menus)
        await message.answer("🚶‍♂️Вы покинули диалог\n\n💡Продолжим поиски нового собеседника")
        await search_user_act(message)
    else:
        await message.answer("🧐Не обнаружил чат с собеседником")

@dp.message_handler(commands="stop")
@dp.message_handler(text='Покинуть чат')
async def leave_from_chat_act(message: types.Message):
    user = await db.get_user(chat=True, user=message.from_user.id)
    print(user)
    if user is not None:
        await db.delete_chat(user=message.from_user.id)
        await db.delete_chat(user=user.interlocutor)
        await bot.send_message(text="😔Пользователь решил покинуть диалог...\n\n💡Продолжим поиск нового собеседника?", chat_id=user.interlocutor, reply_markup=menus)
        await message.answer("🚶‍♂️Вы покинули диалог\n\n💡Продолжим поиски нового собеседника?")
    else:
        await message.answer("🧐Не обнаружил чат с собеседником")
 
 
@dp.message_handler(content_types=["text", "sticker", "photo", "voice", "document"])
async def some_text(message: types.Message):
    user = await db.get_user(chat=True, user=message.from_user.id)
    print(user)
    if user is None:
        await message.answer("🧐Не обнаружил чат с собеседником")
        return
    if message.content_type == "sticker":
        try:
            await bot.send_sticker(chat_id=user.interlocutor, sticker=message.sticker["file_id"])
        except TypeError:
            pass
    elif message.content_type == "photo":
        try:
            await bot.send_photo(chat_id=user.interlocutor, photo=message.photo[len(message.photo) - 1].file_id)
        except TypeError:
            pass
    elif message.content_type == "voice":
        try:
            await bot.send_voice(chat_id=user.interlocutor, voice=message.voice["file_id"])
        except TypeError:
            pass
    elif message.content_type == "document":
        try:
            await bot.send_document(chat_id=user.interlocutor, document=message.document["file_id"])
        except TypeError:
            pass
    else:
        try:
            await bot.send_message(text=message.text, chat_id=user.interlocutor)
        except TypeError:
            pass


async def init_app():
    await async_db_session.init()
    await async_db_session.create_all()

if __name__ == "__main__":
    ioloop = asyncio.get_event_loop()
    ioloop.create_task(init_app())
    tasks = [
        executor.start_polling(dp, skip_updates=True)
    ]
    ioloop.run_until_complete(asyncio.wait(tasks))
    ioloop.close()