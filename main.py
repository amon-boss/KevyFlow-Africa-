import os
import json
from telebot import TeleBot, types
from keep_alive import keep_alive

# === CONFIGURATION VIA VARIABLES D’ENVIRONNEMENT ===
BOT_TOKEN = os.environ['BOT_TOKEN']
CHANNEL_ID = int(os.environ['CHANNEL_ID'])
ADMIN_ID = int(os.environ['ADMIN_ID'])
INVITE_LINK = os.environ['INVITE_LINK']

bot = TeleBot(BOT_TOKEN)
pending_payments = {}

# === DÉMARRAGE DU BOT ===
@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_msg = (
        "👋 Salut et bienvenue sur KevyFlowBot !😎⚔️\n\n"
        "Ce canal est réservé aux membres ayant payé l'accès.🔐\n\n"
        "Étapes à suivre :\n"
        "1️⃣ Choisis ta méthode de paiement 💵\n"
        "2️⃣ Envoie une capture d'écran de ton paiement 🧾\n"
        "3️⃣ On valide et tu seras ajouté ✅"
    )
    bot.send_message(message.chat.id, welcome_msg)
    show_payment_options(message.chat.id)

# === MOYENS DE PAIEMENT ===
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

# === RÉCEPTION DE LA CAPTURE D'ÉCRAN ===
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

# === GESTION DES BOUTONS ===
@bot.callback_query_handler(func=lambda call: True)
def callback_dispatcher(call):
    data = call.data
    if data in [pm[1] for pm in PAYMENT_METHODS]:
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id,
            f"✅ Tu as choisi *{data}*\nEnvoie ta *capture* maintenant.",
            parse_mode='Markdown')

    elif data.startswith("validate_"):
        user_id = int(data.split("_")[1])
        payment = pending_payments.get(user_id)
        if payment:
            username = payment["username"]

            # ✅ Message à l'utilisateur
            bot.send_message(user_id,
                "✅ *Paiement validé*\nBienvenue dans KevyFlow Africa 🌍 !",
                parse_mode='Markdown')

            # 🔗 Envoi du lien avec bouton
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("✅ REJOINS !", callback_data=f"joined_{user_id}_{username}"))
            bot.send_message(user_id, f"{INVITE_LINK}", reply_markup=markup)

            # 📝 Enregistrement dans le fichier membres.json
            membre_data = {
                "username": username,
                "id": user_id
            }

            try:
                with open("data/membres.json", "r") as f:
                    membres = json.load(f)
            except FileNotFoundError:
                membres = []

            if not any(m["id"] == user_id for m in membres):
                membres.append(membre_data)
                with open("data/membres.json", "w") as f:
                    json.dump(membres, f, indent=4)

            del pending_payments[user_id]
            bot.answer_callback_query(call.id, "Utilisateur validé ✅")

    elif data.startswith("refuse_"):
        user_id = int(data.split("_")[1])
        if pending_payments.get(user_id):
            bot.send_message(user_id, "❌ Paiement refusé, vérifie et réessaye.")
            del pending_payments[user_id]
            bot.answer_callback_query(call.id, "Paiement refusé ❌")

    elif data.startswith("joined_"):
        _, user_id, username = data.split("_")
        bot.send_message(CHANNEL_ID, f"🎉 Bienvenue à @{username} dans le canal privé 🔐✨")
        bot.answer_callback_query(call.id, "Bienvenue confirmée ! ✅")

# === MESSAGE PAR DÉFAUT ===
@bot.message_handler(func=lambda message: True)
def fallback(message):
    bot.send_message(message.chat.id, "📸 Envoie une *capture d’écran* de ton paiement.", parse_mode='Markdown')

# === LANCEMENT DU BOT ===
print("KevyFlowBot est actif ✅")
keep_alive()
bot.infinity_polling()
