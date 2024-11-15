import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import random

# Retrieve sensitive data from environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")

if ADMIN_ID is not None:
    ADMIN_ID = int(ADMIN_ID)

# Dictionary to store groups {group_code: {user_id: name}}
groups = {}


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
    group_code = str(random.randint(100000, 999999))  # Generate a unique 6-digit group code

    if group_code in groups:
        await update.message.reply_text("Ein Fehler ist aufgetreten. Versuch es nochmal.")
        return

    groups[group_code] = {}  # Initialize an empty group
    await update.message.reply_text(f"Die Wichtelgruppe '{group_name}' wurde erstellt! Dein Gruppencode ist: {group_code}")


async def join_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /join command: Allows a user to join an existing group."""
    if len(context.args) < 1:
        await update.message.reply_text("Bitte gib den Gruppencode an. Nutzung: /join <Gruppencode>")
        return

    group_code = context.args[0]
    if group_code not in groups:
        await update.message.reply_text("Der angegebene Gruppencode ist ungültig.")
        return

    user_id = update.message.from_user.id
    user_name = update.message.from_user.first_name

    if user_id in groups[group_code]:
        await update.message.reply_text("Du bist bereits Mitglied dieser Gruppe.")
        return

    groups[group_code][user_id] = user_name
    await update.message.reply_text(f"Du bist der Gruppe mit dem Code {group_code} beigetreten! 🎉")


async def list_participants(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /list command: Lists all participants in a group."""
    if len(context.args) < 1:
        await update.message.reply_text("Bitte gib den Gruppencode an. Nutzung: /list <Gruppencode>")
        return

    group_code = context.args[0]
    if group_code not in groups:
        await update.message.reply_text("Der angegebene Gruppencode ist ungültig.")
        return

    if not groups[group_code]:
        await update.message.reply_text("Es gibt noch keine Teilnehmer in dieser Gruppe.")
        return

    participant_list = "\n".join([f"{name}" for name in groups[group_code].values()])
    await update.message.reply_text(f"Aktuelle Teilnehmer in Gruppe {group_code}:\n{participant_list}")


async def assign(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /assign command: Randomly assigns participants to each other."""
    if len(context.args) < 1:
        await update.message.reply_text("Bitte gib den Gruppencode an. Nutzung: /assign <Gruppencode>")
        return

    group_code = context.args[0]
    if group_code not in groups:
        await update.message.reply_text("Der angegebene Gruppencode ist ungültig.")
        return

    if len(groups[group_code]) < 2:
        await update.message.reply_text("Es gibt nicht genug Teilnehmer, um Wichteln durchzuführen!")
        return

    user_ids = list(groups[group_code].keys())
    names = list(groups[group_code].values())

    shuffled_names = names[:]
    random.shuffle(shuffled_names)

    # Ensure no one gets themselves or their Secret Santa
    while True:
        valid = True
        for i in range(len(names)):
            if shuffled_names[i] == names[i]:
                valid = False
            if shuffled_names.index(names[i]) == i:
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

    await update.message.reply_text(f"Wichtel wurden für Gruppe {group_code} zugewiesen!")


async def reset_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /reset command: Resets a group's participants (Admin only)."""
    if len(context.args) < 1:
        await update.message.reply_text("Bitte gib den Gruppencode an. Nutzung: /reset <Gruppencode>")
        return

    group_code = context.args[0]
    if group_code not in groups:
        await update.message.reply_text("Der angegebene Gruppencode ist ungültig.")
        return

    groups[group_code].clear()
    await update.message.reply_text(f"Die Gruppe mit dem Code {group_code} wurde zurückgesetzt.")


def main():
    """Main function to run the bot."""
    if not BOT_TOKEN or not ADMIN_ID:
        print("Fehler: BOT_TOKEN oder ADMIN_ID ist nicht gesetzt.")
        return

    application = Application.builder().token(BOT_TOKEN).build()

    # Register command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("create", create_group))
    application.add_handler(CommandHandler("join", join_group))
    application.add_handler(CommandHandler("list", list_participants))
    application.add_handler(CommandHandler("assign", assign))
    application.add_handler(CommandHandler("reset", reset_group))

    print("Bot wurde gestartet...")
    application.run_polling()


if __name__ == "__main__":
    main()
