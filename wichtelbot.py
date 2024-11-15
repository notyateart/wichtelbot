import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters
import random

# Retrieve sensitive data from environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")  # Admin is identified by their username

# Dictionary to store groups {group_name: {"creator_id": user_id, "members": {user_id: name}}}
groups = {}

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
        context.user_data["command"] = "create"
        return WAITING_FOR_GROUP_NAME

    group_name = " ".join(context.args)
    return await process_create_group(update, context, group_name)


async def process_create_group(update: Update, context: ContextTypes.DEFAULT_TYPE, group_name: str) -> int:
    """Processes the creation of a group."""
    if group_name in groups:
        await update.message.reply_text("Eine Gruppe mit diesem Namen existiert bereits. Bitte wähle einen anderen Namen.")
        return ConversationHandler.END

    user_id = update.message.from_user.id
    groups[group_name] = {"creator_id": user_id, "members": {}}
    await update.message.reply_text(
        f"Die Wichtelgruppe '{group_name}' wurde erstellt! 🎉\n"
        "Wenn du teilnehmen möchtest, benutze /join, um der Gruppe beizutreten.\n\n"
        "Zusätzliche Befehle für dich:\n"
        "/delete - Löscht die Gruppe\n"
        "/assign - Weist alle Teilnehmer zu und schließt die Gruppe"
    )
    return ConversationHandler.END


async def join_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles the /join command: Allows a user to join a group."""
    if len(context.args) < 1:
        await update.message.reply_text("Bitte schicke mir den Gruppennamen:")
        context.user_data["command"] = "join"
        return WAITING_FOR_GROUP_NAME

    group_name = " ".join(context.args)
    return await process_join_group(update, context, group_name)


async def process_join_group(update: Update, context: ContextTypes.DEFAULT_TYPE, group_name: str) -> int:
    """Processes the joining of a group."""
    if group_name not in groups:
        await update.message.reply_text("Der angegebene Gruppenname ist ungültig.")
        return ConversationHandler.END

    user_id = update.message.from_user.id
    if user_id in groups[group_name]["members"]:
        await update.message.reply_text("Du bist bereits Mitglied dieser Gruppe.")
        return ConversationHandler.END

    groups[group_name]["members"][user_id] = update.message.from_user.first_name
    await update.message.reply_text(f"Du bist der Gruppe '{group_name}' beigetreten! 🎉")
    return ConversationHandler.END


async def delete_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles the /delete command: Deletes a group if the user is its creator."""
    if len(context.args) < 1:
        await update.message.reply_text("Bitte schicke mir den Gruppennamen:")
        context.user_data["command"] = "delete"
        return WAITING_FOR_GROUP_NAME

    group_name = " ".join(context.args)
    return await process_delete_group(update, context, group_name)


async def process_delete_group(update: Update, context: ContextTypes.DEFAULT_TYPE, group_name: str) -> int:
    """Processes the deletion of a group."""
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


async def list_participants(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles the /list command: Lists all participants in a group."""
    if len(context.args) < 1:
        await update.message.reply_text("Bitte schicke mir den Gruppennamen:")
        context.user_data["command"] = "list"
        return WAITING_FOR_GROUP_NAME

    group_name = " ".join(context.args)
    return await process_list_participants(update, context, group_name)


async def process_list_participants(update: Update, context: ContextTypes.DEFAULT_TYPE, group_name: str) -> int:
    """Processes listing participants in a group."""
    if group_name not in groups:
        await update.message.reply_text("Der angegebene Gruppenname ist ungültig.")
        return ConversationHandler.END

    if not groups[group_name]["members"]:
        await update.message.reply_text("Es gibt noch keine Teilnehmer in dieser Gruppe.")
        return ConversationHandler.END

    participant_list = "\n".join([f"{name}" for name in groups[group_name]["members"].values()])
    await update.message.reply_text(f"Aktuelle Teilnehmer in Gruppe '{group_name}':\n{participant_list}")
    return ConversationHandler.END


async def receive_group_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles input when waiting for a group name."""
    group_name = update.message.text.strip()
    command = context.user_data.get("command")

    if command == "create":
        return await process_create_group(update, context, group_name)
    elif command == "join":
        return await process_join_group(update, context, group_name)
    elif command == "delete":
        return await process_delete_group(update, context, group_name)
    elif command == "list":
        return await process_list_participants(update, context, group_name)
    else:
        await update.message.reply_text("Ein Fehler ist aufgetreten. Bitte starte erneut.")
        return ConversationHandler.END


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
            CommandHandler("join", join_group),
            CommandHandler("delete", delete_group),
            CommandHandler("list", list_participants),
        ],
        states={
            WAITING_FOR_GROUP_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_group_name),
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
