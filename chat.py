from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message,
    InlineKeyboardButton,
    KeyboardButton,
    FSInputFile,
)
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import Command, CommandObject
from aiogram.filters.state import State, StatesGroup

from models.db_api import methods as db
from models.database import async_db_session
from models.bot import Bots
from models.channel import Channels
from models.user import Users

import asyncio
import logging
import csv

# Define Keyboards
menus = (
    ReplyKeyboardBuilder()
    .add(KeyboardButton(text="Начать поиск"))
    .add(KeyboardButton(text="🫂Партнерка"))
    .add(KeyboardButton(text="🎁Промокод"))
)
dating = (
    ReplyKeyboardBuilder()
    .add(KeyboardButton(text="Продолжить поиск"))
    .add(KeyboardButton(text="Покинуть чат"))
)
searching = ReplyKeyboardBuilder().add(KeyboardButton(text="Остановить поиск"))
ready = ReplyKeyboardBuilder().add(KeyboardButton(text="✅Готово"))
start = ReplyKeyboardBuilder().add(KeyboardButton(text="🤟Стартуем"))

ADMIN = [235519518, 5161665132]

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and storage
bot = Bot(token="5702778958:AAEzOO9p0BIeAKDBlUeXLHwSMqnBaN_Wiu4")
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Define FSM States
class Form(StatesGroup):
    post = State()


@dp.message(Command("stats"), F.from_user.id.in_(ADMIN))
async def stats(message: Message):
    with open("users.csv", "w", encoding="utf-8") as outfile:
        writer = csv.writer(outfile)
        writer.writerow(["id", "user_id", "referals", "user_name", "first_name", "last_name"])
        users = await Users.get_all()
        for user in users:
            try:
                chat = await bot.get_chat(user.user)
                writer.writerow(
                    [user.id, user.user, user.referals, chat.username, chat.first_name, chat.last_name]
                )
            except Exception as e:
                logging.error(e)
    await message.answer_document(FSInputFile("users.csv"))


@dp.message(Command("pub"), F.from_user.id.in_(ADMIN))
async def pub(message: Message, state: FSMContext):
    await message.answer("Send the post")
    await state.set_state(Form.post)


@dp.message(Form.post)
async def post(message: Message, state: FSMContext):
    args = message.html_text.split("\n|button: ")
    text = args[0]
    markup = None
    print(f"Got post: {text}")

    if len(args) > 1:
        markup = InlineKeyboardBuilder()
        for button in args[1:]:
            label, url = button.split("'")
            markup.add(InlineKeyboardButton(text=label, url=url))

    users = await Users.get_all()
    await state.clear()

    for user in users:
        try:
            if message.content_type == "photo":
                await bot.send_photo(
                    user.user, message.photo[-1].file_id, caption=text, reply_markup=markup.as_markup()
                )
            else:
                await bot.send_message(user.user, text, reply_markup=markup.as_markup())
        except Exception as e:
            logging.error(f"{user.user}: {e}")
        await asyncio.sleep(0.4)

    await message.answer("Успешно отправлено")


@dp.message(Command("bot"), F.from_user.id.in_(ADMIN))
async def add_bot(message: Message):
    tokens = message.text.split(" ")
    if len(tokens) < 2:
        await message.answer("Используйте эту команду правильно: /bot token")
        return
    await Bots.create(bot=tokens[1])
    await message.answer("Успешно создана")


@dp.message(Command("channel"), F.from_user.id.in_(ADMIN))
async def add_channel(message: Message):
    args = message.text.split(" ")
    if len(args) < 3 or args[2][0] != "-" or not args[2][1:].isdigit():
        await message.answer("Используйте эту команду правильно: /channel channel_link channel_id")
        return
    await Channels.create(link=args[1], channel=int(args[2]))
    await message.answer("Успешно создана")


@dp.message(Command("bots"), F.from_user.id.in_(ADMIN))
async def all_bots(message: Message):
    bots = await Bots.get_all()
    text = "Вот токены ботов:\n" + "\n".join(bot.bot for bot in bots)
    await message.answer(text)


@dp.message(Command("channels"), F.from_user.id.in_(ADMIN))
async def all_channels(message: Message):
    channels = await Channels.get_all()
    text = "Вот каналы:\n" + "\n".join(channel.link for channel in channels)
    await message.answer(text, disable_web_page_preview=True)


@dp.message(Command("del_bot"), F.from_user.id.in_(ADMIN))
async def delete_bot(message: Message):
    tokens = message.text.split(" ")
    if len(tokens) < 2:
        await message.answer("Используйте эту команду правильно: /del_bot token")
        return
    bot_instance = await Bots.get_bot(bot=tokens[1])
    if bot_instance is None:
        await message.answer("Токен не найден")
        return
    await Bots.delete_bot(bot=tokens[1])
    await message.answer("Успешно удалено")


@dp.message(Command("del_channel"), F.from_user.id.in_(ADMIN))
async def delete_channel(message: Message):
    args = message.text.split(" ")
    if len(args) < 2:
        await message.answer("Используйте эту команду правильно: /del_channel channel_link")
        return
    channel_instance = await Channels.get_channel(link=args[1])
    if channel_instance is None:
        await message.answer("Канал не найден")
        return
    await Channels.delete_channel(link=args[1])
    await message.answer("Успешно удалено")


@dp.message(F.text == "🫂Партнерка")
async def ref(message: Message):
    user = await Users.get(user=message.from_user.id)
    link = f"https://t.me/anonchatlive_bot?start={message.from_user.id}"
    await message.answer(
        f"💡Приглашайте друзей в анонимный чат, и веселитесь вместе!\n\n👥Вы пригласили: {user.referals}\n✅Ваша пригласительная ссылка: {link}"
    )


@dp.message(Command("start"))
@dp.message(F.text == "🤟Стартуем")
async def menu(message: Message, command: CommandObject = None):
    if command is not None:
        args = command.args
    else:
        args = None
    user = await Users.get(user=message.from_user.id)
    if user is None:
        await Users.create(user=message.from_user.id)
        if args and args.isdigit() and int(args) != message.from_user.id:
            print(f"{message.from_user.id} -> {int(args)}")
            ref = await Users.get(user=int(args))
            await Users.updater(int(args), referals=ref.referals + 1)
    await message.answer("🫂Для поиска собеседника напишите /search, или используйте кнопки", reply_markup=menus.as_markup(resize_keyboard=True))


@dp.message(F.text == "✅Готово")
async def check_bots(message: Message):
    bots = await Bots.get_all()
    text = "Нажми Старт в этих ботах, и мы начинаем:\n"
    to_start = []

    for bot_data in bots:
        bot_instance = Bot(token=bot_data.bot)
        try:
            await bot_instance.send_chat_action(message.from_user.id, "typing")
        except Exception as e:
            logging.error(e)
            username = (await bot_instance.get_me()).username
            to_start.append(f"@{username}")
        await bot_instance.session.close()

    if to_start:
        text += "\n".join(to_start)
        await message.answer(text, reply_markup=start.as_markup(resize_keyboard=True))
    else:
        await menu(message)


async def check_channels(message: Message):
    channels = await Channels.get_all()
    to_sub = []
    text = "🥺Для начала поиска, подпишись на каналы моих спонсоров:\n"

    for channel in channels:
        user_status = await bot.get_chat_member(channel.channel, message.from_user.id)
        if user_status.status in ["left", "banned"]:
            to_sub.append(channel.link)

    if to_sub:
        text += "\n".join(to_sub)
        await message.answer(text, reply_markup=ready.as_markup(resize_keyboard=True), disable_web_page_preview=True)
    else:
        await check_bots(message)


@dp.message(F.text == "🎁Промокод")
async def promo(message: Message):
    channels = await Channels.get_all()
    for channel in channels:
        user_status = await bot.get_chat_member(channel.channel, message.from_user.id)
        if user_status.status in ["left", "banned"]:
            await check_channels(message)
            return

    bots = await Bots.get_all()
    for bot_data in bots:
        not_subscribed = False
        bot_instance = Bot(token=bot_data.bot)
        try:
            await bot_instance.send_chat_action(message.from_user.id, "typing")
        except Exception as e:
            logging.error(e)
            not_subscribed = True
        await bot_instance.session.close()

        if not_subscribed:
            await check_bots(message)
            return

    await message.answer("🎁Твой промокод для стикер-бота – anonchat")


@dp.message(Command("search"))
@dp.message(F.text == "Начать поиск")
async def search_user_act(message: Message):
    channels = await Channels.get_all()
    for channel in channels:
        user_status = await bot.get_chat_member(channel.channel, message.from_user.id)
        if user_status.status in ["left", "banned"]:
            await check_channels(message)
            return

    bots = await Bots.get_all()
    for bot_data in bots:
        not_subscribed = False
        bot_instance = Bot(token=bot_data.bot)
        try:
            await bot_instance.send_chat_action(message.from_user.id, "typing")
        except Exception as e:
            logging.error(e)
            not_subscribed = True
        await bot_instance.session.close()

        if not_subscribed:
            await check_bots(message)
            return

    # Handle searching logic
    in_chat = await db.get_user(chat=True, user=message.from_user.id)
    if in_chat:
        await message.answer(
            "🧐Вы уже находитесь в чате с другим пользователем\n\n💡Для начала стоит прекратить текущий диалог"
        )
    else:
        in_queue = await db.get_user(user=message.from_user.id)
        if not in_queue:
            interlocutor = await db.get_user()
            if not interlocutor:
                await db.insert_queue(user=message.from_user.id)
                await message.answer(
                    "🔍Начал искать вам подходящего собеседника, подождите...\n\n💡Вы можете закончить поиск написав /stop_search, или нажав кнопку",
                    reply_markup=searching.as_markup(resize_keyboard=True),
                )
            else:
                await db.delete_queue(user=message.from_user.id)
                await db.delete_queue(user=interlocutor.user)
                await db.insert_chat(user=message.from_user.id, interlocutor=interlocutor.user)
                await db.insert_chat(user=interlocutor.user, interlocutor=message.from_user.id)

                await message.answer("Собеседник найден! Вы можете начать общаться.", reply_markup=dating.as_markup(resize_keyboard=True))
                await bot.send_message(
                    interlocutor.user, "Собеседник найден! Вы можете начать общаться.", reply_markup=dating.as_markup(resize_keyboard=True)
                )
        else:
            await message.answer(
                "🧐Вы уже находитесь в поиске\n\n💡Как только появится собеседник – я вас свяжу"
            )


@dp.message(Command("stop_search"))
@dp.message(F.text == "Остановить поиск")
async def stop_search_act(message: Message):
    user_in_queue = await db.get_user(user=message.from_user.id)
    if user_in_queue:
        await db.delete_queue(user=message.from_user.id)
        await menu(message)
    else:
        await message.answer("❌Вы еще не начали поиск, чтобы его закончить")


@dp.message(Command("next"))
@dp.message(F.text == "Продолжить поиск")
async def next(message: Message):
    in_chat = await db.get_user(chat=True, user=message.from_user.id)
    if in_chat:
        await db.delete_chat(user=message.from_user.id)
        await db.delete_chat(user=in_chat.interlocutor)
        await bot.send_message(
            in_chat.interlocutor,
            "😔Пользователь решил покинуть диалог...\n\n💡Продолжим поиск нового собеседника?",
            reply_markup=menus.as_markup(resize_keyboard=True),
        )
        await message.answer(
            "🚶‍♂️Вы покинули диалог\n\n💡Продолжим поиски нового собеседника"
        )
        await search_user_act(message)
    else:
        await message.answer("🧐Не обнаружил чат с собеседником")


@dp.message(Command("stop"))
@dp.message(F.text == "Покинуть чат")
async def leave_from_chat_act(message: Message):
    in_chat = await db.get_user(chat=True, user=message.from_user.id)
    if in_chat:
        await db.delete_chat(user=message.from_user.id)
        await db.delete_chat(user=in_chat.interlocutor)
        await bot.send_message(
            in_chat.interlocutor,
            "😔Пользователь решил покинуть диалог...\n\n💡Продолжим поиск нового собеседника?",
            reply_markup=menus.as_markup(resize_keyboard=True),
        )
        await message.answer(
            "🚶‍♂️Вы покинули диалог\n\n💡Продолжим поиски нового собеседника?", reply_markup=menus.as_markup(resize_keyboard=True)
        )
    else:
        await message.answer("🧐Не обнаружил чат с собеседником")

# add gifs
@dp.message() # F.content_type.in_(["text", "sticker", "photo", "voice", "document", "video"])
async def some_text(message: Message):
    in_chat = await db.get_user(chat=True, user=message.from_user.id)
    if not in_chat:
        await message.answer("🧐Не обнаружил чат с собеседником")
        return

    try:
        await message.copy_to(in_chat.interlocutor)
        # if message.content_type == "sticker":
        #     await bot.send_sticker(in_chat.interlocutor, message.sticker.file_id)
        # elif message.content_type == "photo":
        #     await bot.send_photo(in_chat.interlocutor, message.photo[-1].file_id)
        # elif message.content_type == "voice":
        #     await bot.send_voice(in_chat.interlocutor, message.voice.file_id)
        # elif message.content_type == "document":
        #     await bot.send_document(in_chat.interlocutor, message.document.file_id)
        # elif message.content_type == "video":
        #     await bot.send_video(in_chat.interlocutor, message.video.file_id)
        # else:
        #     await bot.send_message(in_chat.interlocutor, message.text)
    except Exception as e:
        logging.error(e)


# Initialize application
async def main():
    await async_db_session.init()
    await async_db_session.create_all()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())