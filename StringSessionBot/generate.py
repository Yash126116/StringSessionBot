from telethon import TelegramClient
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from pyrogram.errors import (
    ApiIdInvalid, PhoneNumberInvalid, PhoneCodeInvalid, PhoneCodeExpired,
    SessionPasswordNeeded, PasswordHashInvalid
)
from telethon.errors import (
    ApiIdInvalidError, PhoneNumberInvalidError, PhoneCodeInvalidError,
    PhoneCodeExpiredError, SessionPasswordNeededError, PasswordHashInvalidError
)
from telethon.sessions import StringSession
from asyncio.exceptions import TimeoutError
from data import Data

ask_ques = "Please choose the python library you want to generate string session for"
buttons_ques = [
    [
        InlineKeyboardButton("Pyrogram", callback_data="pyrogram"),
        InlineKeyboardButton("Telethon", callback_data="telethon"),
    ],
    [
        InlineKeyboardButton("Pyrogram Bot", callback_data="pyrogram_bot"),
        InlineKeyboardButton("Telethon Bot", callback_data="telethon_bot"),
    ],
]

@Client.on_message(filters.private & ~filters.forwarded & filters.command('generate'))
async def main(_, msg):
    await msg.reply(ask_ques, reply_markup=InlineKeyboardMarkup(buttons_ques))

async def generate_session(bot: Client, msg: Message, telethon=False, is_bot: bool = False):
    library_type = "Telethon" if telethon else "Pyrogram v2"
    if is_bot:
        library_type += " Bot"
    
    await msg.reply(f"Starting {library_type} Session Generation...")
    user_id = msg.chat.id
    
    # Ask for API ID and API Hash
    api_id, api_hash = await ask_for_api_details(bot, user_id)
    if not api_id or not api_hash:
        return
    
    # Ask for phone number or bot token
    phone_number_msg = await bot.ask(user_id, "Now please send your `PHONE_NUMBER` along with the country code. \nExample: `+19876543210`" if not is_bot else "Now please send your `BOT_TOKEN` \nExample: `12345:abcdefghijklmnopqrstuvwxyz`", filters=filters.text)
    if await cancelled(phone_number_msg):
        return
    phone_number = phone_number_msg.text
    
    await msg.reply("Sending OTP..." if not is_bot else "Logging in as Bot User...")
    
    # Create the client based on the library and user/bot type
    client = create_client(api_id, api_hash, phone_number, telethon, is_bot, user_id)
    await client.connect()
    
    # Handle login and session generation
    string_session = await handle_login_and_generate_session(bot, client, user_id, phone_number, telethon, is_bot)
    if not string_session:
        return
    
    # Send the generated session string to the user
    text = f"**{library_type.upper()} STRING SESSION** \n\n`{string_session}` \n\nGenerated by @StarkStringGenBot"
    await bot.send_message(msg.chat.id, text)
    
    await client.disconnect()
    await bot.send_message(msg.chat.id, f"Successfully generated {library_type} string session.")

async def ask_for_api_details(bot, user_id):
    api_id_msg = await bot.ask(user_id, 'Please send your `API_ID`', filters=filters.text)
    if await cancelled(api_id_msg):
        return None, None
    try:
        api_id = int(api_id_msg.text)
    except ValueError:
        await api_id_msg.reply('Not a valid API_ID (must be an integer). Please start generating session again.', quote=True, reply_markup=InlineKeyboardMarkup(Data.generate_button))
        return None, None
    api_hash_msg = await bot.ask(user_id, 'Please send your `API_HASH`', filters=filters.text)
    if await cancelled(api_hash_msg):
        return None, None
    api_hash = api_hash_msg.text
    return api_id, api_hash

def create_client(api_id, api_hash, phone_number, telethon, is_bot, user_id):
    if telethon and is_bot:
        return TelegramClient(StringSession(), api_id, api_hash)
    elif telethon:
        return TelegramClient(StringSession(), api_id, api_hash)
    elif is_bot:
        return Client(name=f"bot_{user_id}", api_id=api_id, api_hash=api_hash, bot_token=phone_number, in_memory=True)
    else:
        return Client(name=f"user_{user_id}", api_id=api_id, api_hash=api_hash, in_memory=True)

async def handle_login_and_generate_session(bot, client, user_id, phone_number, telethon, is_bot):
    try:
        code = None
        if not is_bot:
            if telethon:
                code = await client.send_code_request(phone_number)
            else:
                code = await client.send_code(phone_number)
    except (ApiIdInvalid, ApiIdInvalidError):
        await bot.send_message(user_id, '`API_ID` and `API_HASH` combination is invalid. Please start generating session again.', reply_markup=InlineKeyboardMarkup(Data.generate_button))
        return None
    except (PhoneNumberInvalid, PhoneNumberInvalidError):
        await bot.send_message(user_id, '`PHONE_NUMBER` is invalid. Please start generating session again.', reply_markup=InlineKeyboardMarkup(Data.generate_button))
        return None

    phone_code = None
    if not is_bot:
        phone_code_msg = await bot.ask(user_id, "Please check for an OTP in your official telegram account. If you got it, send OTP here after reading the format below. \nIf OTP is `12345`, **please send it as** `1 2 3 4 5`.", filters=filters.text, timeout=600)
        if await cancelled(phone_code_msg):
            return None
        phone_code = phone_code_msg.text.replace(" ", "")

    try:
        if not is_bot:
            if telethon:
                await client.sign_in(phone_number, phone_code, password=None)
            else:
                await client.sign_in(phone_number, code.phone_code_hash, phone_code)
        else:
            if telethon:
                await client.start(bot_token=phone_number)
            else:
                await client.sign_in_bot(phone_number)
    except (PhoneCodeInvalid, PhoneCodeInvalidError):
        await bot.send_message(user_id, 'OTP is invalid. Please start generating session again.', reply_markup=InlineKeyboardMarkup(Data.generate_button))
        return None
    except (PhoneCodeExpired, PhoneCodeExpiredError):
        await bot.send_message(user_id, 'OTP is expired. Please start generating session again.', reply_markup=InlineKeyboardMarkup(Data.generate_button))
        return None
    except (SessionPasswordNeeded, SessionPasswordNeededError):
        password_msg = await bot.ask(user_id, 'Your account has enabled two-step verification. Please provide the password.', filters=filters.text, timeout=300)
        if await cancelled(password_msg):
            return None
        password = password_msg.text
        try:
            if telethon:
                await client.sign_in(password=password)
            else:
                await client.check_password(password=password)
        except (PasswordHashInvalid, PasswordHashInvalidError):
            await bot.send_message(user_id, 'Invalid Password Provided. Please start generating session again.', reply_markup=InlineKeyboardMarkup(Data.generate_button))
            return None

    return client.session.save() if telethon else await client.export_session_string()

async def cancelled(msg):
    if "/cancel" in msg.text:
        await msg.reply("Cancelled the Process!", quote=True, reply_markup=InlineKeyboardMarkup(Data.generate_button))
        return True
    elif "/restart" in msg.text:
        await msg.reply("Restarted the Bot!", quote=True, reply_markup=InlineKeyboardMarkup(Data.generate_button))
        return True
    elif msg.text.startswith("/"):  # Bot Commands
        await msg.reply("Cancelled the generation process!", quote=True)
        return True
    else:
        return False