import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters
import random

# Retrieve sensitive data from environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")  # Admin is identified by their username

# Dictionary to store groups {group_name: {"creator_id": user_id, "members": {user_id: name}}}
groups = {}

# Dictionary to store the last active group for each user
user_last_group = {}

# Constants for conversation flow
WAITING_FOR_GROUP_NAME = range(1)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /start command: Welcomes the user and shows available commands."""
    user_username = update.message.from_user.username
    if user_username == ADMIN_USERNAME:
        await update.message.reply_text(
            "Willkommen beim Wichtelbot! 🎁\n\n"
            "Admin-Befehle:\n"
            "/deleteall - Lösche alle Gruppen\n\n"
            "Benutzer-Befehle:\n"
            "/create - Erstelle eine neue Gruppe\n"
            "/delete - Lösche eine Gruppe\n"
            "/assign - Weise Teilnehmer zu\n"
            "/join - Trete einer Gruppe bei\n"
            "/list - Zeige Teilnehmer in der Gruppe"
        )
    else:
        await update.message.reply_text(
            "Willkommen beim Wichtelbot! 🎁\n\n"
            "Verfügbare Befehle:\n"
            "/create - Erstelle eine neue Gruppe\n"
            "/join - Trete einer Gruppe bei\n"
            "/list - Zeige Teilnehmer in der Gruppe"
        )


async def create_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles the /create command: Creates a new group."""
    if len(context.args) < 1:
        await update.message.reply_text("Bitte schicke mir den Gruppennamen:")
        return WAITING_FOR_GROUP_NAME

    group_name = " ".join(context.args)
    if group_name in groups:
        await update.message.reply_text("Eine Gruppe mit diesem Namen existiert bereits. Bitte wähle einen anderen Namen.")
        return ConversationHandler.END

    user_id = update.message.from_user.id
    groups[group_name] = {"creator_id": user_id, "members": {}}
    user_last_group[user_id] = group_name
    await update.message.reply_text(
        f"Die Wichtelgruppe '{group_name}' wurde erstellt! 🎉\n"
        "Wenn du teilnehmen möchtest, benutze /join, um der Gruppe beizutreten.\n\n"
        "Zusätzliche Befehle für dich:\n"
        "/delete - Löscht die Gruppe\n"
        "/assign - Weist alle Teilnehmer zu und schließt die Gruppe"
    )
    return ConversationHandler.END


async def delete_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles the /delete command: Deletes a group if the user is its creator."""
    if len(context.args) < 1:
        await update.message.reply_text("Bitte schicke mir den Gruppennamen:")
        return WAITING_FOR_GROUP_NAME

    group_name = " ".join(context.args)
    if group_name not in groups:
        await update.message.reply_text("Der angegebene Gruppenname ist ungültig.")
        return ConversationHandler.END

    user_id = update.message.from_user.id
    if groups[group_name]["creator_id"] != user_id and update.message.from_user.username != ADMIN_USERNAME:
        await update.message.reply_text("Du bist nicht der Ersteller dieser Gruppe und kannst sie daher nicht löschen.")
        return ConversationHandler.END

    del groups[group_name]
    await update.message.reply_text(f"Die Gruppe '{group_name}' wurde erfolgreich gelöscht.")
    return ConversationHandler.END


async def delete_all_groups(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /deleteall command: Deletes all groups (Admin only)."""
    if update.message.from_user.username != ADMIN_USERNAME:
        await update.message.reply_text("Dieser Befehl ist nur für Admins verfügbar.")
        return

    groups.clear()
    await update.message.reply_text("Alle Gruppen wurden erfolgreich gelöscht.")


async def assign(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles the /assign command: Randomly assigns participants to each other if the user is the group's creator."""
    if len(context.args) < 1:
        await update.message.reply_text("Bitte schicke mir den Gruppennamen:")
        return WAITING_FOR_GROUP_NAME

    group_name = " ".join(context.args)
    if group_name not in groups:
        await update.message.reply_text("Der angegebene Gruppenname ist ungültig.")
        return ConversationHandler.END

    user_id = update.message.from_user.id
    if groups[group_name]["creator_id"] != user_id and update.message.from_user.username != ADMIN_USERNAME:
        await update.message.reply_text("Du bist nicht der Ersteller dieser Gruppe und kannst sie daher nicht zuweisen.")
        return ConversationHandler.END

    if len(groups[group_name]["members"]) < 2:
        await update.message.reply_text("Es gibt nicht genug Teilnehmer, um Wichteln durchzuführen!")
        return ConversationHandler.END

    user_ids = list(groups[group_name]["members"].keys())
    names = list(groups[group_name]["members"].values())

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
            text=f"🎁 Wichtel wurden für Gruppe '{group_name}' zugewiesen!\nDu bist der Wichtel für {recipient}!\nViel Spaß beim Besorgen des Geschenks!"
        )

    # Delete the group after assigning
    del groups[group_name]
    await update.message.reply_text(
        f"Wichtel wurden für Gruppe '{group_name}' erfolgreich zugewiesen! Die Gruppe wurde gelöscht, und der Gruppenname ist wieder verfügbar."
    )
    return ConversationHandler.END


async def process_join_group(update: Update, context: ContextTypes.DEFAULT_TYPE, group_name: str) -> int:
    """Processes the joining of a group."""
    if group_name not in groups:
        await update.message.reply_text("Der angegebene Gruppenname ist ungültig.")
        return ConversationHandler.END

    context.user_data["joining_group"] = group_name
    await update.message.reply_text("Bitte gib deinen Namen ein, um der Gruppe beizutreten:")
    return WAITING_FOR_GROUP_NAME


def main():
    """Main function to run the bot."""
    if not BOT_TOKEN or not ADMIN_USERNAME:
        print("Fehler: BOT_TOKEN oder ADMIN_USERNAME ist nicht gesetzt.")
        return

    application = Application.builder().token(BOT_TOKEN).build()

    # Conversation handler for commands that require group name input
    group_name_handler = ConversationHandler(
        entry_points=[
            CommandHandler("create", create_group),
            CommandHandler("delete", delete_group),
            CommandHandler("deleteall", delete_all_groups),
            CommandHandler("assign", assign),
        ],
        states={
            WAITING_FOR_GROUP_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_join_group),
            ],
        },
        fallbacks=[],
    )

    # Register command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(group_name_handler)

    print("Bot wurde gestartet...")
    application.run_polling()


if __name__ == "__main__":
    main()
