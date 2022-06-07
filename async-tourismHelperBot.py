import asyncio
from syncer import sync
from telebot.async_telebot import AsyncTeleBot
from telebot import types
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
from models import Query, Place, User
from services import getUrlRequest, DAO, getNearbyPlacesAsync, getNearbyPlacesSync

API_TOKEN = "5516917413:AAEsm2SgnOs1UuSSpkeg2PpGZiMSC9rgAJ8"
# -*- coding: utf-8 -*-
"""
This Example will show you how to use register_next_step handler.
"""

bot = AsyncTeleBot(API_TOKEN)


user_dict = {}


# Handle '/start' and '/help'
@bot.message_handler(commands=['help', 'start'])
async def send_welcome(message):
    chat_id = message.chat.id
    if chat_id not in user_dict:
        rep = "Benvenuto. Con questo bot potrai cercare bar, ristoranti a te più vicini, secondo le tue preferenze, semplicemente inviando la tua posizione :)\n Per iniziare, qual è il tuo nome?"
        step = process_name_step
        msg = await bot.reply_to(message, rep)
    else:
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
        markup.row_width = 2
        markup.add(InlineKeyboardButton("tutto", callback_data="restaurant|bar|food"),
                   InlineKeyboardButton("ristorante", callback_data="restaurant"),
                   InlineKeyboardButton("cibo", callback_data="food"))
        rep = f"Ciao, {user_dict['chat_id'].name}, che tipo di attività stai cercando?"
        msg = await bot.reply_to(message, rep, reply_markup=markup)
        bot.register_next_step_handler(msg, process_placeType_step)
        step = process_placeType_step
    bot.register_next_step_handler(msg, step)


async def process_name_step(message):
    try:
        chat_id = message.chat.id
        if not chat_id in user_dict:
            name = message.text
            user = User(name=name)
            user.id = chat_id
            user_dict[chat_id] = user

        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
        markup.row_width = 2
        markup.add(InlineKeyboardButton("tutto"),
                   InlineKeyboardButton("ristorante"),
                   InlineKeyboardButton("cibo")
                   )
        msg = await bot.reply_to(message, f"Bene, {user_dict[chat_id].name}, che tipo di attività stai cercando?", reply_markup=markup)
        bot.register_next_step_handler(msg, process_placeType_step)
    except Exception as e:
        print(e)
        await bot.reply_to(message, 'Errore!')


async def process_placeType_step(message):
    try:
        chat_id = message.chat.id
        #restaurant|bar|food
        if message.text == "tutto":
            placeType = "restaurant|bar|food"
        elif message.text == "ristorante":
            placeType = "restaurant"
        elif message.text == "bar":
            placeType = "bar"
        elif message.text == "cibo":
            placeType = "food"
        else:
            msg = await bot.reply_to(message, 'Input errato, riprova!')
            bot.register_next_step_handler(msg, process_placeType_step)
            return

        user = user_dict[chat_id]
        user.query.placeType = placeType

        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
        markup.row_width = 2
        markup.add(InlineKeyboardButton("Qualsiasi prezzo", callback_data="qualsiasi"),
                   InlineKeyboardButton("1", callback_data="1"),
                   InlineKeyboardButton("2", callback_data="2"),
                   InlineKeyboardButton("3", callback_data="3"),
                   InlineKeyboardButton("4", callback_data="4")
                   ),
        msg = await bot.reply_to(message, 'Quanto vuoi spendere al massimo su una scala da 1 a 4? ', reply_markup=markup)
        bot.register_next_step_handler(msg, process_priceLevel_step)
    except Exception as e:
        print(e)
        await bot.reply_to(message, 'Errore, riprova!')


async def process_priceLevel_step(message):
    try:
        chat_id = message.chat.id
        price_level = message.text
        user = user_dict[chat_id]
        user.query.maxprice = price_level
        if message.text == "Qualsiasi prezzo":
            price_level=""
        else:
            try:
                if not (int(price_level) >= 1) and (int(price_level) <= 4):
                    msg = await bot.reply_to(message, 'Valore errato! Deve essere compreso tra 1 e 4! Riprova')
                    bot.register_next_step_handler(msg, process_priceLevel_step)
            except ValueError as e:
                msg = await bot.reply_to(message, 'Errore! Valore errato, riprova')
                bot.register_next_step_handler(msg, process_priceLevel_step)

        msg = bot.send_message(chat_id, 'Ok, adesso inviami la tua posizione ')
        bot.register_next_step_handler(msg, process_getLocation_step)
    except Exception as e:
        print(e)
        msg = await bot.reply_to(message, 'Errore!')
        bot.register_next_step_handler(msg, process_priceLevel_step)


async def process_getLocation_step(message):
    try:
        chat_id = message.chat.id
        longitude = message.location.longitude
        latitude = message.location.latitude
        user = user_dict[chat_id]
        user.query.latitude = latitude
        user.query.longitude = longitude

        """ finire
        fare query
        fare dao"""

        #bot.send_message(chat_id, 'Questi sono i risultati, --- ')
        json = await getNearbyPlacesSync(lat=user.query.latitude, lon=user.query.longitude, placeType=user.query.placeType )
        objects_places = DAO(json)
        risposta = ""
        for place in objects_places:

            # f"nome attività: {place.name}\nLatitudine: {place.lat}\nLongitudine: {place.long}"
            risposta += f"nome attività: {place.name}\nLatitudine: {place.lat}\nLongitudine: {place.long}\n\n"
        bot.send_message(chat_id, risposta) #test
    except Exception as e:
        await bot.reply_to(message, 'Errore!')
        print(e)


# Enable saving next step handlers to file "./.handlers-saves/step.save".
# Delay=2 means that after any change in next step handlers (e.g. calling register_next_step_handler())
# saving will hapen after delay 2 seconds.
#bot.enable_save_next_step_handlers(delay=2)

# Load next_step_handlers from save file (async default "./.handlers-saves/step.save")
# WARNING It will work only if enable_save_next_step_handlers was called!
#bot.load_next_step_handlers()


asyncio.run(bot.polling())
