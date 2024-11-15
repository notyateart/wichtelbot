import os
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
import random

# Retrieve sensitive data from environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")

if ADMIN_ID is not None:
    ADMIN_ID = int(ADMIN_ID)

# Dictionary to store groups {group_code: {user_id: name}}
groups = {}

# The rest of the code remains unchanged...

def main():
    """Hauptfunktion zum Ausführen des Bots."""
    if not BOT_TOKEN or not ADMIN_ID:
        print("Fehler: BOT_TOKEN oder ADMIN_ID ist nicht gesetzt.")
        return

    updater = Updater(BOT_TOKEN)
    dispatcher = updater.dispatcher

    # Handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("create", create_group))
    dispatcher.add_handler(CommandHandler("join", join_group))
    dispatcher.add_handler(CommandHandler("list", list_participants))
    dispatcher.add_handler(CommandHandler("assign", assign))
    dispatcher.add_handler(CommandHandler("reset", reset_group))

    # Startet den Bot
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
