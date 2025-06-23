import os
import time
import threading
from telebot import TeleBot, types
from keep_alive import keep_alive

BOT_TOKEN = os.environ['BOT_TOKEN']
CHANNEL_ID = int(os.environ['CHANNEL_ID'])
ADMIN_ID = int(os.environ['ADMIN_ID'])
INVITE_LINK = os.environ['INVITE_LINK']

bot = TeleBot(BOT_TOKEN)
pending_payments = {}

PAYMENT_NUMBERS = {
    "Orange Money": "+2250768388770",
    "MTN Money": "+2250504652480",
    "Wave": "+2250768388770"
}

PAYMENT_METHODS = [
    ("🟠 Orange Money 💰", "Orange Money"),
    ("🟡 MTN Money 💰", "MTN Money"),
    ("🔵 WAVE 💰", "Wave")
]

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_msg = (
        "👋 Salut et bienvenue sur KevyFlowBot !😎⚔️\n\n"
        "Ce canal est réservé aux membres ayant payé l'accès🔐\n\n"
        "🎟️ PRIX À PAYER: 2500F\n\n"
        "Étapes à suivre pour payer:\n"
        "1️⃣ Choisissez une méthode de paiement 💵\n"
        "2️⃣ Envoyez une capture d'écran du paiement 🧾\n"
        "3️⃣ Votre capture sera traitée, après validation vous serez ajouté ✅"
    )
    bot.send_message(message.chat.id, welcome_msg)
    show_payment_options(message.chat.id)

def show_payment_options(chat_id):
    markup = types.InlineKeyboardMarkup()
    for label, value in PAYMENT_METHODS:
        markup.add(types.InlineKeyboardButton(label, callback_data=value))
    bot.send_message(chat_id, "Choisis ta méthode de paiement ⬇️", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_dispatcher(call):
    data = call.data
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    username = call.from_user.username or call.from_user.first_name

    if data in [pm[1] for pm in PAYMENT_METHODS]:
        number = PAYMENT_NUMBERS[data]
        bot.answer_callback_query(call.id)
        if data == "Wave":
            bot.send_message(chat_id,
                f"✅ Vous avez choisi {data}.\n\n"
                f"Veuillez effectuer le paiement sur ce numéro : {number}.\n"
                f"Faites ensuite une capture d'écran et envoyez-la ici. 🤝\nJe vous attends ☺️🙏🏼")
        else:
            bot.send_message(chat_id,
                f"✅ Vous avez choisi {data}.\n\n"
                f"Veuillez effectuer le paiement sur ce numéro : {number}.\n"
                f"Faites ensuite une capture d'écran et envoyez-la ici. 🤝\nJe vous attends ☺️🙏🏼")

    elif data.startswith("validate_"):
        user_id = int(data.split("_")[1])
        payment = pending_payments.get(user_id)
        if payment:
            bot.send_message(user_id,
                "🎉 Félicitations !\n"
                "Ta capture a été validée avec succès.\n"
                "Clique sur le bouton ci-dessous pour rejoindre le canal privé 👇🏼")

            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("✅ REJOINDRE", url=INVITE_LINK, callback_data=f"join_{user_id}_{payment['username']}"))
            bot.send_message(user_id, "⬇️ Appuie ici :", reply_markup=markup)

            # Démarre la vérification après 5 secondes
            threading.Thread(target=check_user_joined, args=(user_id, payment['username'])).start()

            del pending_payments[user_id]
            bot.answer_callback_query(call.id, "Utilisateur validé ✅")

    elif data.startswith("refuse_"):
        user_id = int(data.split("_")[1])
        if pending_payments.get(user_id):
            bot.send_message(user_id, "😩 Dommage !\nPaiement refusé, vérifie et réessaye.")
            del pending_payments[user_id]
            bot.answer_callback_query(call.id, "Paiement refusé ❌")

@bot.message_handler(content_types=['photo'])
def handle_screenshot(message):
    bot.send_message(message.chat.id, "🕵️ Merci ! Ta preuve est en cours de validation.")
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    file_id = message.photo[-1].file_id
    pending_payments[user_id] = {"file_id": file_id, "username": username}
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ Valider", callback_data=f"validate_{user_id}"),
        types.InlineKeyboardButton("❌ Refuser", callback_data=f"refuse_{user_id}")
    )
    caption = f"🧾 *Preuve reçue*\n👤 @{username}\n🆔 ID: {user_id}"
    try:
        bot.send_photo(ADMIN_ID, file_id, caption=caption, parse_mode='Markdown', reply_markup=markup)
    except Exception as e:
        bot.send_message(ADMIN_ID, f"⚠️ Erreur lors de l'envoi de la preuve : {e}")

def check_user_joined(user_id, username):
    time.sleep(5)
    try:
        member = bot.get_chat_member(CHANNEL_ID, user_id)
        if member.status in ['member', 'administrator', 'creator']:
            bot.send_message(CHANNEL_ID, f"🎉 Bienvenue à @{username} dans le canal privé 🔐✨")
    except Exception as e:
        print(f"Erreur lors de la vérification d'adhésion : {e}")

@bot.message_handler(func=lambda message: True)
def fallback(message):
    bot.send_message(message.chat.id, "📸 Envoie une *capture d’écran* de ton paiement.", parse_mode='Markdown')

print("KevyFlowBot est actif ✅")
keep_alive()
bot.infinity_polling()
