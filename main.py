from flask import Flask
from keep_alive import keep_alive
from telebot import TeleBot, types
import os
from datetime import datetime
import pytz
import threading
import time

bot = TeleBot(os.getenv("BOT_TOKEN"))
ADMIN_ID = int(os.getenv("ADMIN_ID"))
GROUP_ID = int(os.getenv("GROUP_ID"))
INVIT_LINK = os.getenv("INVIT_LINK")

confirmed_users = set()

# Message /start
@bot.message_handler(commands=["start"])
def welcome_user(message):
    welcome = """👋 Salut et bienvenue sur KevyFlowBot !😎⚔️

Ce groupe est réservé aux membres ayant payé l'accès 🔐

🎟️ PRIX À PAYER: 2500F

Étapes à suivre pour payer:
1️⃣ Choisissez une méthode de paiement 💵
2️⃣ Envoyez une capture d'écran du paiement 🧾
3️⃣ Votre capture sera traitée, après validation vous serez ajouté ✅
"""
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn1 = types.InlineKeyboardButton("🟠 Orange Money 💰", callback_data="orange")
    btn2 = types.InlineKeyboardButton("🟡 MTN Money 💰", callback_data="mtn")
    btn3 = types.InlineKeyboardButton("🔵 Wave 💰", callback_data="wave")
    markup.add(btn1, btn2, btn3)
    bot.send_message(message.chat.id, welcome, reply_markup=markup)

# Choix du paiement
@bot.callback_query_handler(func=lambda call: call.data in ["orange", "wave", "mtn"])
def handle_payment(call):
    numbers = {
        "orange": "+2250768388770",
        "wave": "+2250768388770",
        "mtn": "+2250504652480"
    }
    names = {
        "orange": "🟠Orange Money💰",
        "wave": "🔵Wave💰",
        "mtn": "🟡MTN Money💰"
    }
    number = numbers[call.data]
    name = names[call.data]

    text = f"""✅ Vous avez choisi {name}

Veuillez effectuer le paiement sur ce numéro :
`{number}`

Ensuite, envoyez une capture d'écran du paiement ici 🧾.
Je vous attends ☺️🙏🏼"""
    bot.send_message(call.message.chat.id, text, parse_mode="Markdown")

# Réception des captures
@bot.message_handler(content_types=["photo"])
def handle_payment_proof(message):
    if message.chat.type == "private":
        caption = f"""🧾 Nouvelle capture reçue !

👤 Utilisateur : @{message.from_user.username or message.from_user.first_name}
🆔 ID : {message.from_user.id}

Que souhaitez-vous faire ?"""
        markup = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton("✅ Valider", callback_data=f"valider_{message.from_user.id}")
        btn2 = types.InlineKeyboardButton("❌ Refuser", callback_data=f"refuser_{message.from_user.id}")
        markup.add(btn1, btn2)
        bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=caption, reply_markup=markup)

# Réponse à la validation ou refus
@bot.callback_query_handler(func=lambda call: call.data.startswith("valider_") or call.data.startswith("refuser_"))
def handle_validation(call):
    user_id = int(call.data.split("_")[1])
    if call.data.startswith("valider_"):
        text = """🎉 Félicitations !
Ta capture a été validée avec succès.

Clique sur le bouton ci-dessous pour rejoindre le groupe privé 👇🏼"""
        markup = types.InlineKeyboardMarkup()
        join = types.InlineKeyboardButton("🔓 Rejoindre le groupe", url=INVIT_LINK)
        markup.add(join)
        bot.send_message(user_id, text, reply_markup=markup)
    else:
        bot.send_message(user_id, "😩 Dommage ! Ta capture a été refusée. Réessaie ou contacte le support.")

# Bienvenue et aurevoir
@bot.my_chat_member_handler()
def handle_members(update):
    chat_id = update.chat.id
    if chat_id != GROUP_ID:
        return

    new_status = update.new_chat_member.status
    old_status = update.old_chat_member.status
    user = update.from_user

    if new_status == "member":
        text = f"""🎉 Bienvenue @{user.username or user.first_name} dans *KevyFlow Africa 🌍* !

Tu es ici pour gagner, progresser et te surpasser 💸🔥  
👥 Membres actuels, cliquez sur des réactions pour lui souhaiter la bienvenue !"""
        bot.send_message(GROUP_ID, text, parse_mode="Markdown")

    elif new_status == "left":
        goodbye = f"👋 @{user.username or user.first_name} nous a quittés. On espère te revoir bientôt 😔"
        bot.send_message(GROUP_ID, goodbye)

# Messages auto matin et nuit
def send_morning():
    text = """☀️ Bonjour la famille 🤠

Aujourd’hui, c’est un nouveau jour pour de nouveaux gains !  
Bonne humeur, bonne vibes et concentration 🔥🎯

🗳️ *Prêt pour les gains d’aujourd’hui ?* 🤞🏼🥲"""
    poll = {
        "question": "Prêt pour les gains d’aujourd’hui ? 🤞🏼🥲",
        "options": ["Oui 🫂😋", "Non 🙂‍↔️😩", "Dans un instant 🕝😎"]
    }
    bot.send_message(GROUP_ID, text, parse_mode="Markdown")
    bot.send_poll(GROUP_ID, poll["question"], poll["options"])

def send_night():
    text = """🌙 Bonne nuit à tous la team KevyFlow 🌍

📌 Qui ne risque rien 🙅🏼‍♂️ n'a rien ❌  
C'est quand tu sais pas que t'es en danger que t'es en danger 😎

🗳️ *La journée a été ?*"""
    poll = {
        "question": "La journée a été ?",
        "options": ["✅ De gains", "❌ De pertes", "🌀 Moyenne"]
    }
    bot.send_message(GROUP_ID, text, parse_mode="Markdown")
    bot.send_poll(GROUP_ID, poll["question"], poll["options"])

# Boucle de planification
def schedule_loop():
    tz = pytz.timezone("Africa/Abidjan")
    while True:
        now = datetime.now(tz)
        if now.hour == 7 and now.minute == 30:
            send_morning()
        if now.hour == 23 and now.minute == 0:
            send_night()
        time.sleep(60)

# Lancement
keep_alive()
threading.Thread(target=schedule_loop).start()
bot.infinity_polling()
