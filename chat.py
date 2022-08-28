from email.message import Message
from aiogram import Bot, Dispatcher, types, executor
from aiogram.dispatcher.filters import IDFilter
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext

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

ready = ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton('✅Готово'))

start = ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton('🤟Стартуем'))


ADMIN = [235519518, 5161665132]

logging.basicConfig(level=logging.INFO)
bot = Bot(token="5702778958:AAEzOO9p0BIeAKDBlUeXLHwSMqnBaN_Wiu4")
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

class Form(StatesGroup):
    post = State()


@dp.message_handler(IDFilter(chat_id=ADMIN), commands="pub")
async def pub(message: types.Message):
    await message.answer('Send the post')
    await Form.post.set()


@dp.message_handler(state=Form.post, content_types=['photo', 'text'])
async def post(message: types.Message, state: FSMContext):
    arg = message.html_text.split('\n|button: ')
    msg = arg[0]
    markup = None
    if len(msg) < 5:
        await message.answer('Слишком короткий')
        return
    if len(arg) > 1:
        markup = InlineKeyboardMarkup()
        for i in arg[1:]:
            i = i.split("'")
            markup.add(InlineKeyboardButton(i[0], i[1]))
    users = await Users.get_all()
    await state.finish()
    for i in users:
        if message.content_type == 'photo':
            try:
                await bot.send_photo(i.user, message.photo[len(message.photo) - 1].file_id, caption=msg, reply_markup=markup)
            except Exception as e:
                print(e)
        else:
            try:
                await bot.send_message(i.user, msg, reply_markup=markup)
            except Exception as e:
                print(e)
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
    if len(msg) < 3 or msg[2][0] != '-' or not msg[2][1:].isdigit():
        await message.answer('Используйте эту команду правильно: /channel channel_link channel_id')
        return
    await Channels.create(link=msg[1], channel=int(msg[2]))
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
        text += i.link+'\n'
    await message.answer(text, disable_web_page_preview=True)

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
    if len(msg) < 2:
        await message.answer("Используйте эту команду правильно: /del_channel channel_link")
        return
    channel = await Channels.get_channel(link=msg[1])
    if channel is None:
        await message.answer("Канал не найден")
        return
    await Channels.delete_channel(link=msg[1])
    await message.answer("Успешно удалено")

@dp.message_handler(commands="start")
@dp.message_handler(text='🤟Стартуем')
async def menu(message: types.Message):
    if message.text == '🤟Стартуем':
        text = 'Нажми Старт в этих ботах, и мы начинаем:\n'
        bots = await Bots.get_all()
        to_start = []
        for i in bots:
            bot2 = Bot(token=i.bot)
            try:
                await bot2.send_chat_action(message.from_user.id, 'typing')
            except Exception as e:
                print(e)
                username = (await bot2.get_me()).username
                to_start.append('@'+username)
            sess = await bot2.get_session()
            await sess.close()
        if len(to_start) > 0:
            for i in to_start:
                text += i+'\n'
            await message.answer(text, reply_markup=start)
            return
        else:
            pass
    user = await Users.get(user=message.from_user.id)
    print(user)
    if user is None:
        await Users.create(user=message.from_user.id)
    await message.answer("🫂Для поиска собеседника напишите /search, или используйте кнопки", reply_markup=menus)


@dp.message_handler(text='✅Готово')
async def check_bots(message: types.Message, text=''):
    bots = await Bots.get_all()
    to_start = []
    if message.text == '✅Готово':
        channels = await Channels.get_all()
        to_sub = []
        text2 = '🥺Для начала поиска, подпишись на каналы моих спонсоров:\n'
        for i in channels:
            user = await bot.get_chat_member(i.channel, message.from_user.id)
            if user.status == 'left' or user.status == 'banned':
                to_sub.append(i.link)
        
        if len(to_sub) > 0:
            for i in to_sub:
                text2 += i+'\n'
            await message.answer(text2, reply_markup=ready, disable_web_page_preview=True)
            return
        else:
            text += "😉Супер, спасибо! А теперь, предстоит ещё один шаг! "
    text += 'Нажми Старт в этих ботах, и мы начинаем:\n'

    for i in bots:
        bot2 = Bot(token=i.bot)
        try:
            await bot2.send_chat_action(message.from_user.id, 'typing')
        except Exception as e:
            print(e)
            username = (await bot2.get_me()).username
            to_start.append('@'+username)
        sess = await bot2.get_session()
        await sess.close()
    
        
    if len(to_start) > 0:
        for i in to_start:
            text += i+'\n'
    else:
        await menu(message)
        return
        
    await message.answer(text, reply_markup=start)


async def check_channels(message: types.Message):
    channels = await Channels.get_all()
    to_sub = []
    text = '🥺Для начала поиска, подпишись на каналы моих спонсоров:\n'
    
    for i in channels:
        user = await bot.get_chat_member(i.channel, message.from_user.id)
        if user.status == 'left' or user.status == 'banned':
            to_sub.append(i.link)
        
    if len(to_sub) > 0:
        for i in to_sub:
            text += i+'\n'
    else:
        await check_bots(message)
        return
        
    await message.answer(text, reply_markup=ready, disable_web_page_preview=True)


@dp.message_handler(commands="search")
@dp.message_handler(text=['Начать поиск'])
async def search_user_act(message: types.Message):
    bots = await Bots.get_all()
    channels = await Channels.get_all()
    for i in channels:
        user = await bot.get_chat_member(i.channel, message.from_user.id)
        if user.status == 'left' or user.status == 'banned':
            await check_channels(message)
            return
    
    for i in bots:
        not_sub = False
        bot2 = Bot(token=i.bot)
        try:
            await bot2.send_chat_action(message.from_user.id, 'typing')
        except Exception as e:
            print(e)
            not_sub = True
        sess = await bot2.get_session()
        await sess.close()
        if not_sub:
            await check_bots(message)
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
        await message.answer("🚶‍♂️Вы покинули диалог\n\n💡Продолжим поиски нового собеседника?", reply_markup=menus)
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
