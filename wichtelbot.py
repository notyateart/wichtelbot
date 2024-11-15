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

def start(update: Update, context: CallbackContext) -> None:
    """Start-Befehl: Begrüßt Benutzer."""
    update.message.reply_text(
        "Willkommen beim Wichtelbot! 🎁\n"
        "Erstelle eine neue Wichtelgruppe mit /create <Gruppenname>.\n"
        "Oder tritt einer bestehenden Gruppe mit /join <Gruppencode> bei."
    )

def create_group(update: Update, context: CallbackContext) -> None:
    """Erstellt eine neue Wichtelgruppe."""
    if len(context.args) < 1:
        update.message.reply_text("Bitte gib einen Gruppennamen an. Nutzung: /create <Gruppenname>")
        return

    group_name = " ".join(context.args)
    group_code = str(random.randint(100000, 999999))  # Generiere einen einzigartigen 6-stelligen Code

    if group_code in groups:
        update.message.reply_text("Ein Fehler ist aufgetreten. Versuch es nochmal.")
        return

    groups[group_code] = {}  # Initialisiere eine leere Gruppe
    update.message.reply_text(f"Die Wichtelgruppe '{group_name}' wurde erstellt! Dein Gruppencode ist: {group_code}")

def join_group(update: Update, context: CallbackContext) -> None:
    """Tritt einer bestehenden Wichtelgruppe bei."""
    if len(context.args) < 1:
        update.message.reply_text("Bitte gib den Gruppencode an. Nutzung: /join <Gruppencode>")
        return

    group_code = context.args[0]
    if group_code not in groups:
        update.message.reply_text("Der angegebene Gruppencode ist ungültig.")
        return

    user_id = update.message.from_user.id
    user_name = update.message.from_user.first_name

    if user_id in groups[group_code]:
        update.message.reply_text("Du bist bereits Mitglied dieser Gruppe.")
        return

    groups[group_code][user_id] = user_name
    update.message.reply_text(f"Du bist der Gruppe mit dem Code {group_code} beigetreten! 🎉")

def list_participants(update: Update, context: CallbackContext) -> None:
    """Zeigt alle Teilnehmer einer Gruppe."""
    if len(context.args) < 1:
        update.message.reply_text("Bitte gib den Gruppencode an. Nutzung: /list <Gruppencode>")
        return

    group_code = context.args[0]
    if group_code not in groups:
        update.message.reply_text("Der angegebene Gruppencode ist ungültig.")
        return

    if not groups[group_code]:
        update.message.reply_text("Es gibt noch keine Teilnehmer in dieser Gruppe.")
        return

    participant_list = "\n".join([f"{name}" for name in groups[group_code].values()])
    update.message.reply_text(f"Aktuelle Teilnehmer in Gruppe {group_code}:\n{participant_list}")

def assign(update: Update, context: CallbackContext) -> None:
    """Wählt Wichtel innerhalb einer Gruppe aus."""
    if len(context.args) < 1:
        update.message.reply_text("Bitte gib den Gruppencode an. Nutzung: /assign <Gruppencode>")
        return

    group_code = context.args[0]
    if group_code not in groups:
        update.message.reply_text("Der angegebene Gruppencode ist ungültig.")
        return

    if len(groups[group_code]) < 2:
        update.message.reply_text("Es gibt nicht genug Teilnehmer, um Wichteln durchzuführen!")
        return

    user_ids = list(groups[group_code].keys())
    names = list(groups[group_code].values())

    shuffled_names = names[:]
    random.shuffle(shuffled_names)

    # Sicherstellen, dass niemand sich selbst oder seinen Wichtel hat
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

    # Teilnehmer benachrichtigen
    for user_id, recipient in assignments.items():
        context.bot.send_message(
            chat_id=user_id,
            text=f"🎁 Du bist der Wichtel für {recipient}! Viel Spaß beim Besorgen des Geschenks!"
        )

    update.message.reply_text(f"Wichtel wurden für Gruppe {group_code} zugewiesen!")

def reset_group(update: Update, context: CallbackContext) -> None:
    """Setzt eine Gruppe zurück (nur Admin)."""
    if len(context.args) < 1:
        update.message.reply_text("Bitte gib den Gruppencode an. Nutzung: /reset <Gruppencode>")
        return

    group_code = context.args[0]
    if group_code not in groups:
        update.message.reply_text("Der angegebene Gruppencode ist ungültig.")
        return

    groups[group_code].clear()
    update.message.reply_text(f"Die Gruppe mit dem Code {group_code} wurde zurückgesetzt.")

def main():
    """Hauptfunktion zum Ausführen des Bots."""
    print("Bot wurde gestartet...")
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
