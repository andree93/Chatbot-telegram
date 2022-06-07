import re
import telebot
from jproperties import Properties
from telebot import types
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup,ReplyKeyboardRemove
from models import Query, Place, User
from services import getUrlRequest, DAO, getNearbyPlacesAsync, getNearbyPlacesSync


configs = Properties()
with open('app-config.properties', 'rb') as config_file:
    configs.load(config_file)

API_TOKEN = configs.get("API_TOKEN_TELEGRAM").data
# -*- coding: utf-8 -*-

bot = telebot.TeleBot(API_TOKEN, parse_mode="HTML")

user_dict = dict()

# Handle '/start' and '/help'
@bot.message_handler(commands=['help', 'start'])
def send_welcome(message):
    chat_id = message.chat.id
    rep = "Benvenuto. Con questo bot potrai cercare bar, ristoranti a te più vicini, secondo le tue preferenze, semplicemente inviando la tua posizione :)\nPer iniziare, qual è il tuo nome?"
    step = process_name_step
    msg = bot.reply_to(message, rep, reply_markup=ReplyKeyboardRemove())
    # if chat_id not in user_dict:
    #     rep = "Benvenuto. Con questo bot potrai cercare bar, ristoranti a te più vicini, secondo le tue preferenze, semplicemente inviando la tua posizione :)\n Per iniziare, qual è il tuo nome?"
    #     step = process_name_step
    #     msg = bot.reply_to(message, rep)
    # else:
    #     # markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    #     # markup.row_width = 2
    #     # markup.add(InlineKeyboardButton("tutto", callback_data="restaurant|bar|food"),
    #     #            InlineKeyboardButton("ristorante", callback_data="restaurant"),
    #     #            InlineKeyboardButton("cibo", callback_data="food"))
    #     # rep = f"Ciao, {user_dict['chat_id'].name}, che tipo di attività stai cercando?"
    #     # msg = bot.reply_to(message, rep, reply_markup=markup)
    #     # bot.register_next_step_handler(msg, process_placeType_step)
    #     # step = process_placeType_step
    bot.register_next_step_handler(msg, step)



@bot.message_handler(commands=['riavvia_ricerca'])
def send_restart(message):
    chat_id = message.chat.id
    rep = "Quale tipo di attività stai cercando?"
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    markup.row_width = 2
    markup.add(InlineKeyboardButton("tutto", callback_data="restaurant|bar|food"),
                InlineKeyboardButton("ristorante", callback_data="restaurant"),
                InlineKeyboardButton("cibo", callback_data="food"))
    msg = bot.reply_to(message, rep, reply_markup=markup)
    bot.register_next_step_handler(msg, process_placeType_step)



@bot.message_handler(commands=['cambia_nome'])
def cambia_nome(message):
    chat_id = message.chat.id
    msg = bot.reply_to(message, "Inserisci un nuovo nome")
    bot.register_next_step_handler(msg, process_name_step)



def process_name_step(message):
    try:
        chat_id = message.chat.id
        name = message.text
        if chat_id not in user_dict.keys() or user_dict[chat_id].name != name:
            if name.startswith("/"):
                msg = bot.reply_to(message, "Errore, riscrivi il tuo nome per favore!")
                bot.register_next_step_handler(msg, process_name_step)
                return
            user = User(name=name)
            user.id = chat_id
            user_dict[chat_id] = user

        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
        markup.row_width = 2
        markup.add(InlineKeyboardButton("tutto"),
                   InlineKeyboardButton("ristorante"),
                   InlineKeyboardButton("cibo")
                   )
        msg = bot.reply_to(message, f"Bene, {user_dict[chat_id].name}, che tipo di attività stai cercando?", reply_markup=markup)
        bot.register_next_step_handler(msg, process_placeType_step)
    except Exception as e:
        print(e)
        bot.reply_to(message, 'Errore! - Step name')



def process_placeType_step(message):
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
            msg = bot.reply_to(message, 'Input errato, riprova!')
            bot.register_next_step_handler(msg, process_placeType_step)
            return

        user = user_dict[chat_id]
        user.query.placeType = placeType

        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
        markup.row_width = 1
        markup.add(InlineKeyboardButton("Qualsiasi prezzo", callback_data="qualsiasi"),
                   InlineKeyboardButton("1", callback_data="1"),
                   InlineKeyboardButton("2", callback_data="2"),
                   InlineKeyboardButton("3", callback_data="3"),
                   InlineKeyboardButton("4", callback_data="4")
                   ),
        msg = bot.reply_to(message, 'Quanto vuoi spendere al massimo su una scala da 1 a 4? ', reply_markup=markup)
        bot.register_next_step_handler(msg, process_priceLevel_step)
    except Exception as e:
        print(e)
        bot.reply_to(message, 'Errore, riprova!')


@bot.message_handler(regexp="^\d")
def process_priceLevel_step(message):
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
                    msg = bot.reply_to(message, 'Valore errato! Deve essere compreso tra 1 e 4! Riprova')
                    bot.register_next_step_handler(msg, process_priceLevel_step)
            except ValueError as e:
                msg = bot.reply_to(message, 'Errore! Valore errato, riprova')
                bot.register_next_step_handler(msg, process_priceLevel_step)

        msg = bot.send_message(chat_id, 'Ok, adesso inviami la tua posizione', reply_markup=ReplyKeyboardRemove())
        bot.register_next_step_handler(msg, process_getLocation_step)
    except Exception as e:
        print(e)
        msg = bot.reply_to(message, 'Errore!')
        bot.register_next_step_handler(msg, process_priceLevel_step)


@bot.message_handler(content_types=["location"])
def process_getLocation_step(message):
    try:
        chat_id = message.chat.id
        user = user_dict[chat_id]
        position = message.location
        if position is not None:
            longitude = position.longitude
            latitude = position.latitude
            user.query.latitude = latitude
            user.query.longitude = longitude

        

        #bot.send_message(chat_id, 'Questi sono i risultati, --- ')
        user_dict[chat_id].query.places = DAO(getNearbyPlacesSync(lat=user.query.latitude, lon=user.query.longitude, placeType=user.query.placeType ))

        markups = [InlineKeyboardButton(f"Cod-{str(i)}", callback_data=f"Cod-{str(i)}") for i in
                   range(1, len(user_dict[chat_id].query.places)+1)]
        markups.append(InlineKeyboardButton( "/riavvia_ricerca") )
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
        markup.row_width = 2
        markup.add(*markups)

        risposta = "Ho trovato le seguenti attività nei tuoi dintorni:\n"
        placeN = 1
        if len(user_dict[chat_id].query.places) > 1:
            for place in user_dict[chat_id].query.places:
                risposta += f"<b>Codice</b>: {placeN}\n<b>Nome</b>: {place.name}\n<b>Punteggio</b>: {place.rating}\n<b>Zona</b>: {place.vicinity}\n\n"
                placeN +=1
            risposta+="\n Ottieni la posizione della località di tuo interesse cliccando il relativo nome sulla tastiera, oppure riavvia la ricerca con /riavvia_ricerca"
            msg = bot.send_message(chat_id, risposta, reply_markup=markup) #test
            bot.register_next_step_handler(msg, send_location)
        else:
            bot.send_message(chat_id,
                             "Spiacente, nessun risultato trovato! riprova con il comando /riavvia_ricerca",
                             reply_markup=ReplyKeyboardRemove())
    except Exception as e:
        print(e)
        bot.reply_to(message, 'Errore!', reply_markup=ReplyKeyboardRemove())




@bot.message_handler(regexp="^Cod-\d\d")
def send_location(message):
    chat_id = message.chat.id

    if len(message.text)>0:
        if message.text == "/riavvia_ricerca":
            markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
            markup.row_width = 2
            markup.add(InlineKeyboardButton("tutto", callback_data="restaurant|bar|food"),
                       InlineKeyboardButton("ristorante", callback_data="restaurant"),
                       InlineKeyboardButton("cibo", callback_data="food"))
            msg = bot.reply_to(message, "Quale tipo di attività stai cercando?", reply_markup=markup)
            bot.register_next_step_handler(msg, process_placeType_step)
        else:
            try:
                id_location_requested = int(re.search("\d+", message.text).group(0))
                if ((id_location_requested >= 1) and (id_location_requested <= len(user_dict[chat_id].query.places))):
                    bot.send_location(chat_id, user_dict[chat_id].query.places[id_location_requested - 1].lat, user_dict[chat_id].query.places[id_location_requested - 1].long)
                    msg = bot.send_message(chat_id, "Puoi raggiungere la località richiesta cliccando sulla posizione\nOppure puoi richiederne un'altra dalla tastiera, o riavviare la ricerca con il comando /riavvia_ricerca")
                    bot.register_next_step_handler(msg, send_location)
                else:
                    msg = bot.send_message(chat_id, "Errore, il codice inviato non risulta valido. Riprova!")
                    bot.register_next_step_handler(msg, send_location)
            except:
                msg = bot.send_message(chat_id,
                                       "Errore, Input non valido. Riprova!")
                bot.register_next_step_handler(msg, send_location)
    else:
        bot.send_message(chat_id, "Errore, input non valido!")



@bot.message_handler(commands=['cambia_nome'])
def cambia_nome(message):
    chat_id = message.chat.id
    msg = bot.reply_to(message, "Inserisci un nuovo nome")
    bot.register_next_step_handler(msg, process_name_step)

# Enable saving next step handlers to file "./.handlers-saves/step.save".
# Delay=2 means that after any change in next step handlers (e.g. calling register_next_step_handler())
# saving will hapen after delay 2 seconds.
#bot.enable_save_next_step_handlers(delay=2)

# Load next_step_handlers from save file (default "./.handlers-saves/step.save")
# WARNING It will work only if enable_save_next_step_handlers was called!
#bot.load_next_step_handlers()

bot.infinity_polling()
