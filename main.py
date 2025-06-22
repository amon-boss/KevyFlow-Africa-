import os
from telebot import TeleBot, types
from keep_alive import keep_alive

# === CONFIGURATION PAR VARIABLES D’ENVIRONNEMENT ===
BOT_TOKEN = os.environ['BOT_TOKEN']
CHANNEL_ID = int(os.environ['CHANNEL_ID'])
ADMIN_ID = int(os.environ['ADMIN_ID'])
INVITE_LINK = os.environ['INVITE_LINK']

bot = TeleBot(BOT_TOKEN)
pending_payments = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_msg = (
        "👋 Salut et bienvenue sur KevyFlowBot !😎⚔️\n\n"
        "Ce canal est réservé aux membres ayant payé l'accès 🔐\n\n"
        "🎟️ *PRIX À PAYER:* 3000F\n\n"
        "Étapes à suivre pour payer :\n"
        "1️⃣ Choisissez une méthode de paiement 💵\n"
        "2️⃣ Envoyez une capture d'écran du paiement 🧾\n"
        "3️⃣ Votre capture sera traitée, après validation vous serez ajouté ✅"
    )
    bot.send_message(message.chat.id, welcome_msg, parse_mode='Markdown')
    show_payment_options(message.chat.id)

PAYMENT_METHODS = [
    ("🟠 Orange Money 💰", "Orange Money"),
    ("🟡 MTN Money 💰", "MTN Money"),
    ("🟢 Moov Money 💰", "Moov Money"),
    ("🔵 WAVE 💰", "Wave")
]

def show_payment_options(chat_id):
    markup = types.InlineKeyboardMarkup()
    for label, value in PAYMENT_METHODS:
        markup.add(types.InlineKeyboardButton(label, callback_data=value))
    bot.send_message(chat_id, "Choisis ta méthode de paiement ⬇️", reply_markup=markup)

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
        bot.send_message(ADMIN_ID, f"⚠️ Erreur envoi de la preuve de @{username} (ID {user_id})\nErreur: {e}")

@bot.callback_query_handler(func=lambda call: True)
def callback_dispatcher(call):
    data = call.data
    if data in [pm[1] for pm in PAYMENT_METHODS]:
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id,
            f"✅ Vous avez choisi *{data}*.\n"
            "Veuillez effectuer le paiement, faire une capture d'écran du paiement et m'envoyer la capture ici.🤝\n"
            "Je vous attends ☺️🙏🏼",
            parse_mode='Markdown')

    elif data.startswith("validate_"):
        user_id = int(data.split("_")[1])
        payment = pending_payments.get(user_id)
        if payment:
            bot.send_message(user_id,
                "🎉 *Félicitations !*\n"
                "Ton accès a été validé avec succès.\n"
                "Clique sur le bouton ci-dessous pour rejoindre le canal privé 👇🏼",
                parse_mode='Markdown',
                reply_markup=types.InlineKeyboardMarkup().add(
                    types.InlineKeyboardButton("✅ REJOINDRE KEVYFLOW AFRICA", url=INVITE_LINK)
                ))
            del pending_payments[user_id]
            bot.answer_callback_query(call.id, "Utilisateur validé ✅")

    elif data.startswith("refuse_"):
        user_id = int(data.split("_")[1])
        if pending_payments.get(user_id):
            bot.send_message(user_id, "😩 *Dommage !*\nTon paiement n'a pas été validé. Merci de vérifier et réessayer.", parse_mode='Markdown')
            del pending_payments[user_id]
            bot.answer_callback_query(call.id, "Paiement refusé ❌")

    elif data.startswith("joined_"):
        _, user_id, username = data.split("_")
        bot.send_message(CHANNEL_ID, f"🎉 Bienvenue à @{username} dans le canal privé 🔐✨")
        bot.answer_callback_query(call.id, "Bienvenue confirmée ! ✅")

@bot.message_handler(func=lambda message: True)
def fallback(message):
    bot.send_message(message.chat.id, "📸 Envoie une *capture d’écran* de ton paiement.", parse_mode='Markdown')

print("KevyFlowBot est actif ✅")
keep_alive()
bot.infinity_polling()
