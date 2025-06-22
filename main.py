import os
from telebot import TeleBot, types
from keep_alive import keep_alive

BOT_TOKEN = os.environ['BOT_TOKEN']
CHANNEL_ID = int(os.environ['CHANNEL_ID'])
ADMIN_ID = int(os.environ['ADMIN_ID'])
INVITE_LINK = os.environ['INVITE_LINK']

bot = TeleBot(BOT_TOKEN)
pending_payments = {}

# Méthodes de paiement
PAYMENT_METHODS = {
    "Orange Money": "+2250768388770",
    "MTN Money": "+2250504652480",
    "Wave": "https://pay.wave.com/m/M_ci_pxo6yO3yloZ6/c/ci/?amount=2500"
}

# START
@bot.message_handler(commands=['start'])
def send_welcome(message):
    text = (
        "👋 Salut et bienvenue sur KevyFlowBot !😎⚔️\n\n"
        "Ce canal est réservé aux membres ayant payé l'accès🔐\n\n"
        "🎟️ PRIX À PAYER: 2500F\n\n"
        "Étapes à suivre pour payer:\n"
        "1️⃣ Choisisez une méthode de paiement 💵\n"
        "2️⃣ Envoyez une capture d'écran du paiement 🧾\n"
        "3️⃣ Votre capture sera traitée, après validation vous serez ajouté ✅"
    )
    markup = types.InlineKeyboardMarkup()
    for label in PAYMENT_METHODS:
        markup.add(types.InlineKeyboardButton(label, callback_data=label))
    bot.send_message(message.chat.id, text, reply_markup=markup)

# CHOIX MÉTHODE DE PAIEMENT
@bot.callback_query_handler(func=lambda call: call.data in PAYMENT_METHODS)
def handle_payment_method(call):
    method = call.data
    chat_id = call.message.chat.id

    if method == "Wave":
        bot.answer_callback_query(call.id, url=PAYMENT_METHODS[method])
        bot.send_message(chat_id,
            f"✅ Vous avez choisi *{method}*.\n\n"
            f"Veuillez effectuer le paiement via le lien sécurisé ci-dessous 👇🏼\n"
            f"{PAYMENT_METHODS[method]}\n\n"
            "📸 Ensuite, fais une capture d'écran et envoie-la ici pour validation 🤝\n"
            "Je t’attends ☺️🙏🏼", parse_mode="Markdown")
    else:
        num = PAYMENT_METHODS[method]
        bot.send_message(chat_id,
            f"✅ Vous avez choisi *{method}*.\n\n"
            f"Le numéro de paiement **{num}** a été copié dans ton presse-papier automatiquement.\n"
            "Effectue le paiement, fais une capture d'écran et envoie-la ici. 🤝\n"
            "Je t’attends ☺️🙏🏼", parse_mode="Markdown")
        bot.send_message(chat_id, f"`{num}`", parse_mode='Markdown')

# RÉCEPTION DE LA CAPTURE
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

# VALIDATION / REFUS / BIENVENUE
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    data = call.data

    # Validation
    if data.startswith("validate_"):
        user_id = int(data.split("_")[1])
        payment = pending_payments.get(user_id)

        if payment:
            username = payment['username']
            msg = (
                "🎉 *Félicitations !*\n"
                "Ta capture a été validée avec succès.\n"
                "Clique sur le premier bouton ci-dessous pour rejoindre le canal privé 👇🏼\n"
                "Dès que tu rejoins, clique sur le deuxième bouton pour recevoir ton message de bienvenue directement dans le canal ☺️🎉"
            )
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("✅ REJOINDRE LE CANAL", url=INVITE_LINK))
            markup.add(types.InlineKeyboardButton("✅ J’AI REJOINT", callback_data=f"joined_{user_id}_{username}"))
            bot.send_message(user_id, msg, reply_markup=markup, parse_mode="Markdown")
            bot.answer_callback_query(call.id, "Utilisateur validé ✅")
            del pending_payments[user_id]
        else:
            bot.answer_callback_query(call.id, "Preuve introuvable.")

    # Refus
    elif data.startswith("refuse_"):
        user_id = int(data.split("_")[1])
        if pending_payments.get(user_id):
            bot.send_message(user_id, "😩 *Dommage !*\nTa preuve a été refusée. Vérifie bien et renvoie-la.", parse_mode="Markdown")
            del pending_payments[user_id]
            bot.answer_callback_query(call.id, "Paiement refusé ❌")

    # Bienvenue dans le canal
    elif data.startswith("joined_"):
        try:
            _, user_id, username = data.split("_")
            bot.send_message(CHANNEL_ID, f"🎉 Bienvenue @{username} dans le canal privé 🔐✨")
            bot.answer_callback_query(call.id, "Bienvenue confirmée ✅")
        except:
            bot.answer_callback_query(call.id, "Erreur d’identification.")

# Message par défaut
@bot.message_handler(func=lambda message: True)
def fallback(message):
    bot.send_message(message.chat.id, "📸 Envoie une *capture d’écran* de ton paiement.", parse_mode='Markdown')

# Lancer le bot
print("KevyFlowBot est actif ✅")
keep_alive()
bot.infinity_polling()
