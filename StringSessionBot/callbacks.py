import traceback
from data import Data
from pyrogram import Client
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup
from StringSessionBot.generate import generate_session, ask_ques, buttons_ques

OWNER_ID = 1237293986  # Replace with the actual owner ID

# Callbacks
@Client.on_callback_query()
async def _callbacks(bot: Client, callback_query: CallbackQuery):
    user = await bot.get_me()
    mention = user.mention
    query = callback_query.data.lower()
    if query.startswith("home"):
        if query == 'home':
            chat_id = callback_query.from_user.id
            message_id = callback_query.message.id
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=Data.START.format(callback_query.from_user.mention, mention),
                reply_markup=InlineKeyboardMarkup(Data.buttons),
            )
    elif query == "about":
        chat_id = callback_query.from_user.id
        message_id = callback_query.message.id
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=Data.ABOUT,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(Data.home_buttons),
        )
    elif query == "help":
        chat_id = callback_query.from_user.id
        message_id = callback_query.message.id
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=Data.HELP,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(Data.home_buttons),
        )
    elif query == "generate":
        await callback_query.answer()
        await callback_query.message.reply(ask_ques, reply_markup=InlineKeyboardMarkup(buttons_ques))
    elif query.startswith("pyrogram") or query.startswith("telethon"):
        try:
            if query == "pyrogram":
                await generate_session(bot, callback_query.message)
            elif query == "pyrogram_bot":
                await callback_query.answer("Please note that this bot session will be of pyrogram v2", show_alert=True)
                await generate_session(bot, callback_query.message, is_bot=True)
            elif query == "telethon_bot":
                await callback_query.answer()
                await generate_session(bot, callback_query.message, telethon=True, is_bot=True)
            elif query == "telethon":
                await callback_query.answer()
                await generate_session(bot, callback_query.message, telethon=True)
        except Exception as e:
            error_message = ERROR_MESSAGE.format(str(e))
            user_info = callback_query.from_user
            user_details = f"User: {user_info.first_name} {user_info.last_name or ''} (@{user_info.username or 'No Username'})\nUser ID: {user_info.id}"
            print(traceback.format_exc())
            await bot.send_message(
                chat_id=OWNER_ID,
                text=f"An error occurred in @Session_Generation_bot:\n\n{str(e)}\n\nTraceback:\n{traceback.format_exc()}\n\nUser Details:\n{user_details}",
            )

ERROR_MESSAGE = (
    "Oops! An exception occurred! \n\n**Error** : {} "
)