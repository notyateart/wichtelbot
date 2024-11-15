import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters
import random

# Retrieve sensitive data from environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")  # Admin is identified by their username

# Dictionary to store groups {group_name: {"creator_id": user_id, "members": {user_id: name}}}
groups = {}

# Dictionary to store the current group for each user {user_id: group_name}
user_current_group = {}

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
            "/leave - Verlasse eine Gruppe\n"
            "/list - Zeige Teilnehmer in der Gruppe"
        )
    else:
        await update.message.reply_text(
            "Willkommen beim Wichtelbot! 🎁\n\n"
            "Verfügbare Befehle:\n"
            "/create - Erstelle eine neue Gruppe\n"
            "/join - Trete einer Gruppe bei\n"
            "/leave - Verlasse eine Gruppe\n"
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
    if user_id in user_current_group:
        await update.message.reply_text(
            "Du bist bereits in einer Gruppe. Bitte verlasse deine aktuelle Gruppe mit /leave, um eine neue Gruppe zu erstellen."
        )
        return ConversationHandler.END

    groups[group_name] = {"creator_id": user_id, "members": {user_id: update.message.from_user.first_name}}
    user_current_group[user_id] = group_name
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
    if user_id in user_current_group:
        await update.message.reply_text(
            f"Du bist bereits in der Gruppe '{user_current_group[user_id]}'. Bitte verlasse sie mit /leave, um einer neuen Gruppe beizutreten."
        )
        return ConversationHandler.END

    groups[group_name]["members"][user_id] = update.message.from_user.first_name
    user_current_group[user_id] = group_name
    await update.message.reply_text(f"Du bist der Gruppe '{group_name}' beigetreten! 🎉")
    return ConversationHandler.END


async def leave_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /leave command: Allows a user to leave their current group."""
    user_id = update.message.from_user.id
    if user_id not in user_current_group:
        await update.message.reply_text("Du bist derzeit in keiner Gruppe.")
        return

    group_name = user_current_group.pop(user_id)
    groups[group_name]["members"].pop(user_id)

    # Check if the group is empty and delete it
    if not groups[group_name]["members"]:
        del groups[group_name]
        await update.message.reply_text(
            f"Die Gruppe '{group_name}' wurde gelöscht, da keine Mitglieder mehr vorhanden sind."
        )
    else:
        await update.message.reply_text(f"Du hast die Gruppe '{group_name}' verlassen.")


async def delete_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles the /delete command: Deletes a group if the user is its creator."""
    user_id = update.message.from_user.id
    group_name = user_current_group.get(user_id)

    if not group_name or group_name not in groups:
        await update.message.reply_text("Du hast keine Gruppe erstellt, die du löschen kannst.")
        return ConversationHandler.END

    if groups[group_name]["creator_id"] != user_id:
        await update.message.reply_text("Du bist nicht der Ersteller dieser Gruppe und kannst sie daher nicht löschen.")
        return ConversationHandler.END

    del groups[group_name]
    user_current_group.pop(user_id, None)

    for member_id, member_group in list(user_current_group.items()):
        if member_group == group_name:
            user_current_group.pop(member_id)

    await update.message.reply_text(f"Die Gruppe '{group_name}' wurde erfolgreich gelöscht.")
    return ConversationHandler.END


async def assign(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles the /assign command: Randomly assigns participants to each other."""
    user_id = update.message.from_user.id
    group_name = user_current_group.get(user_id)

    if not group_name or group_name not in groups:
        await update.message.reply_text("Du hast keine Gruppe, der du Teilnehmer zuweisen kannst.")
        return ConversationHandler.END

    if groups[group_name]["creator_id"] != user_id:
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
    for member_id in list(user_current_group.keys()):
        if user_current_group[member_id] == group_name:
            user_current_group.pop(member_id)

    await update.message.reply_text(
        f"Wichtel wurden für Gruppe '{group_name}' erfolgreich zugewiesen! Die Gruppe wurde gelöscht."
    )
    return ConversationHandler.END


def main():
    """Main function to run the bot."""
    if not BOT_TOKEN or not ADMIN_USERNAME:
        print("Fehler: BOT_TOKEN oder ADMIN_USERNAME ist nicht gesetzt.")
        return

    application = Application.builder().token(BOT_TOKEN).build()

    # Register command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("create", create_group))
    application.add_handler(CommandHandler("join", join_group))
    application.add_handler(CommandHandler("leave", leave_group))
    application.add_handler(CommandHandler("delete", delete_group))
    application.add_handler(CommandHandler("assign", assign))

    print("Bot wurde gestartet...")
    application.run_polling()


if __name__ == "__main__":
    main()
