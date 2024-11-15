import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters
import random

# Retrieve sensitive data from environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Dictionary to store groups {group_name: {user_id: name}}
groups = {}

# Dictionary to store the last active group for each user
user_last_group = {}

# Constants for conversation flow
WAITING_FOR_ID = range(1)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /start command: Welcomes the user."""
    await update.message.reply_text(
        "Willkommen beim Wichtelbot! 🎁\n"
        "Erstelle eine neue Wichtelgruppe mit /create <Gruppenname>.\n"
        "Oder tritt einer bestehenden Gruppe mit /join <Gruppencode> bei."
    )


async def create_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /create command: Creates a new group."""
    if len(context.args) < 1:
        await update.message.reply_text("Bitte gib einen Gruppennamen an. Nutzung: /create <Gruppenname>")
        return

    group_name = " ".join(context.args)
    if group_name in groups:
        await update.message.reply_text("Eine Gruppe mit diesem Namen existiert bereits. Bitte wähle einen anderen Namen.")
        return

    groups[group_name] = {}  # Initialize an empty group
    user_last_group[update.message.from_user.id] = group_name
    await update.message.reply_text(
        f"Die Wichtelgruppe '{group_name}' wurde erstellt! 🎉\n"
        "Wenn du teilnehmen möchtest, benutze /join <Gruppenname>, um der Gruppe beizutreten."
    )


async def join_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles the /join command: Allows a user to join a group."""
    if len(context.args) < 1:
        await update.message.reply_text("Bitte gib den Gruppennamen an.")
        return WAITING_FOR_ID

    group_name = " ".join(context.args)
    if group_name not in groups:
        await update.message.reply_text("Der angegebene Gruppenname ist ungültig.")
        return ConversationHandler.END

    context.user_data["joining_group"] = group_name
    await update.message.reply_text("Bitte gib deinen Namen ein, um der Gruppe beizutreten:")
    return WAITING_FOR_ID


async def receive_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receives the name from the user and adds them to the group."""
    group_name = context.user_data.get("joining_group")
    if not group_name or group_name not in groups:
        await update.message.reply_text("Ein Fehler ist aufgetreten. Bitte starte den Beitritt erneut mit /join.")
        return ConversationHandler.END

    user_id = update.message.from_user.id
    user_name = update.message.text

    if user_id in groups[group_name]:
        await update.message.reply_text("Du bist bereits Mitglied dieser Gruppe.")
        return ConversationHandler.END

    groups[group_name][user_id] = user_name
    user_last_group[user_id] = group_name
    await update.message.reply_text(f"Du bist der Gruppe '{group_name}' beigetreten! 🎉")
    return ConversationHandler.END


async def list_participants(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /list command: Lists all participants in a group."""
    user_id = update.message.from_user.id
    group_name = user_last_group.get(user_id)

    if not group_name or group_name not in groups:
        await update.message.reply_text("Du bist derzeit mit keiner Gruppe verbunden.")
        return

    if not groups[group_name]:
        await update.message.reply_text("Es gibt noch keine Teilnehmer in dieser Gruppe.")
        return

    participant_list = "\n".join([f"{name}" for name in groups[group_name].values()])
    await update.message.reply_text(f"Aktuelle Teilnehmer in Gruppe '{group_name}':\n{participant_list}")


async def assign(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /assign command: Randomly assigns participants to each other."""
    user_id = update.message.from_user.id
    group_name = user_last_group.get(user_id)

    if not group_name or group_name not in groups:
        await update.message.reply_text("Du bist derzeit mit keiner Gruppe verbunden.")
        return

    if len(groups[group_name]) < 2:
        await update.message.reply_text("Es gibt nicht genug Teilnehmer, um Wichteln durchzuführen!")
        return

    user_ids = list(groups[group_name].keys())
    names = list(groups[group_name].values())

    shuffled_names = names[:]
    random.shuffle(shuffled_names)

    # Ensure no one gets themselves
    while True:
        valid = True
        for i in range(len(names)):
            if shuffled_names[i] == names[i]:
                valid = False
        if valid:
            break
        random.shuffle(shuffled_names)

    assignments = {user_ids[i]: shuffled_names[i] for i in range(len(user_ids))}

    # Notify participants of their assignments
    for user_id, recipient in assignments.items():
        await context.bot.send_message(
            chat_id=user_id,
            text=f"🎁 Du bist der Wichtel für {recipient}! Viel Spaß beim Besorgen des Geschenks!"
        )

    # Notify admin and delete the group
    del groups[group_name]
    await update.message.reply_text(
        f"Wichtel wurden für Gruppe '{group_name}' erfolgreich zugewiesen! Die Gruppe wurde gelöscht, und der Gruppenname ist wieder verfügbar."
    )


def main():
    """Main function to run the bot."""
    if not BOT_TOKEN:
        print("Fehler: BOT_TOKEN ist nicht gesetzt.")
        return

    application = Application.builder().token(BOT_TOKEN).build()

    # Conversation handler for joining a group
    join_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("join", join_group)],
        states={
            WAITING_FOR_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_name)],
        },
        fallbacks=[],
    )

    # Register command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("create", create_group))
    application.add_handler(join_conv_handler)
    application.add_handler(CommandHandler("list", list_participants))
    application.add_handler(CommandHandler("assign", assign))

    print("Bot wurde gestartet...")
    application.run_polling()


if __name__ == "__main__":
    main()
