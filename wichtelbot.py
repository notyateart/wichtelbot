import os
import json
import random
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# Get environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")

# Persistent data file paths
GROUPS_FILE = "groups.json"
PREFERENCES_FILE = "preferences.json"

# Load or initialize data
def load_data(file_path, default):
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            return json.load(f)
    return default

def save_data(file_path, data):
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)

groups = load_data(GROUPS_FILE, {})
preferences = load_data(PREFERENCES_FILE, {})

# Data structures
user_to_group = {}  # Maps user IDs to their current group

# Command: /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.message.from_user
    response = "🎄 Willkommen beim Wichtel-Bot! Hier sind die verfügbaren Befehle:\n\n"

    # Participant section
    response += "👤 Teilnehmer:\n"
    response += "/join [Gruppenname] - Einer Gruppe beitreten\n"
    response += "/leave - Gruppe verlassen\n"
    response += "/status - Gruppendetails anzeigen\n"
    response += "/preference - Deine Vorlieben angeben oder löschen\n\n"

    # Group creator section
    response += "👑 Gruppen-Ersteller:\n"
    response += "/create [Gruppenname] - Neue Gruppe erstellen\n"
    response += "/delete [Gruppenname] - Gruppe löschen\n"
    response += "/assign - Wichtel zuweisen (Kreislogik)\n\n"

    # Admin section (only visible to admin user)
    if user.username == ADMIN_USERNAME:
        response += "🔧 Admin:\n"
        response += "/showallgroups - Alle Gruppen anzeigen\n"
        response += "/deleteallgroups - Alle Gruppen löschen\n"

    await update.message.reply_text(response)

# Command: /create
async def create_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("⚠️ Bitte gib einen Gruppennamen an. Beispiel: /create MeineGruppe")
        return

    group_name = context.args[0]
    if group_name in groups:
        await update.message.reply_text("⚠️ Diese Gruppe existiert bereits.")
        return

    groups[group_name] = {"creator": update.message.from_user.id, "participants": {}}
    save_data(GROUPS_FILE, groups)
    await update.message.reply_text(
        f"✅ Gruppe '{group_name}' wurde erstellt!\n"
        f"Nutze /join {group_name}, um der Gruppe beizutreten."
    )

# Command: /join
async def join_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("⚠️ Bitte gib einen Gruppennamen an. Beispiel: /join MeineGruppe")
        return

    group_name = context.args[0]
    user_id = update.message.from_user.id

    if user_id in user_to_group:
        current_group = user_to_group[user_id]
        await update.message.reply_text(
            f"⚠️ Du bist bereits in der Gruppe '{current_group}'. Verlasse die aktuelle Gruppe mit /leave, bevor du einer neuen Gruppe beitrittst."
        )
        return

    if group_name not in groups:
        await update.message.reply_text("⚠️ Diese Gruppe existiert nicht.")
        return

    # Get the user's Telegram name
    telegram_name = (
        update.message.from_user.full_name
        or update.message.from_user.first_name
        or None
    )

    if telegram_name:
        groups[group_name]["participants"][user_id] = telegram_name
        user_to_group[user_id] = group_name
        save_data(GROUPS_FILE, groups)
        await update.message.reply_text(
            f"✅ Du bist der Gruppe '{group_name}' als '{telegram_name}' beigetreten."
        )
    else:
        await update.message.reply_text("🎅 Ich konnte deinen Namen nicht finden. Bitte sende mir deinen Namen:")
        context.user_data["current_group"] = group_name
        return 1  # Move to fallback state if name is unknown

# Command: /leave
async def leave_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id

    if user_id not in user_to_group:
        await update.message.reply_text("⚠️ Du bist in keiner Gruppe.")
        return

    group_name = user_to_group[user_id]
    del groups[group_name]["participants"][user_id]
    del user_to_group[user_id]

    if not groups[group_name]["participants"]:
        del groups[group_name]
        save_data(GROUPS_FILE, groups)
        await update.message.reply_text(
            f"✅ Du hast die Gruppe '{group_name}' verlassen. "
            "⚠️ Die Gruppe wurde gelöscht, da keine Teilnehmer mehr vorhanden sind."
        )
    else:
        save_data(GROUPS_FILE, groups)
        await update.message.reply_text(
            f"✅ Du hast die Gruppe '{group_name}' verlassen."
        )

# Command: /status
async def group_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id

    if user_id not in user_to_group:
        await update.message.reply_text("⚠️ Du bist in keiner Gruppe.")
        return

    group_name = user_to_group[user_id]
    participants = groups[group_name]["participants"]

    if not participants:
        await update.message.reply_text(f"⚠️ Die Gruppe '{group_name}' hat keine Teilnehmer.")
        return

    names = "\n".join(f"- {name}" for name in participants.values() if name)
    await update.message.reply_text(
        f"📜 Deine aktuelle Gruppe: '{group_name}'\n"
        f"👥 Teilnehmer:\n{names}"
    )

# Command: /set-preference
async def set_preference(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id

    # Save new preference
    preference = " ".join(context.args)
    preferences[user_id] = preference
    save_data(PREFERENCES_FILE, preferences)
    await update.message.reply_text(f"✅ Deine Vorlieben wurden gespeichert: {preference}")

# Command: /delete-preference
async def del_preference(update: Update, context: ContextTypes.DEFUAL_TYPE) -> None:
    user_id = update.message.from_user.id

    # Delete preference
    if user_id in preferences:
        del preferences[user_id]
        save_data(PREFERENCES_FILE, preferences)
        await update.message.reply_text("✅ Deine Vorlieben wurden gelöscht.")
    else:
        await update.message.reply_text("⚠️ Du hattest keine gespeicherten Vorlieben.")
    return

# Command: /assign
async def assign_circle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id

    if user_id not in user_to_group:
        await update.message.reply_text("⚠️ Du bist in keiner Gruppe.")
        return

    group_name = user_to_group[user_id]
    if groups[group_name]["creator"] != user_id:
        await update.message.reply_text("⚠️ Nur der Ersteller der Gruppe kann Teilnehmer zuweisen.")
        return

    participants = list(groups[group_name]["participants"].values())
    if len(participants) < 2:
        await update.message.reply_text("⚠️ Es müssen mindestens 2 Teilnehmer in der Gruppe sein.")
        return

    # Shuffle participants for randomness
    random.shuffle(participants)

    # Create the circular assignments
    assignments = {participants[i]: participants[(i + 1) % len(participants)] for i in range(len(participants))}

    # Notify each participant of their assigned recipient and show preferences
    for user_id, name in groups[group_name]["participants"].items():
        receiver = assignments.get(name, "keinen")
        preference = preferences.get(user_id, "Keine angegeben")
        await context.bot.send_message(
            chat_id=user_id,
            text=f"🎄 Dein Wichtel ist: {receiver} 🎅\n"
                 f"🎁 Falls {receiver} Vorlieben angegeben hat siehst du sie hier:\n{preference}"
                 f"\n\nDas Wichteln ist nun abgeschlossen. Viel Spaß beim Schenken!"
        )

    # Delete the group after assignments
    del groups[group_name]
    del user_to_group[user_id]
    save_data(GROUPS_FILE, groups)
    await update.message.reply_text(
        f"✅ Wichtel wurden erfolgreich zugewiesen! \n🎅 Die Gruppe '{group_name}' wurde gelöscht."
    )

async def admin_show_groups(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_name = update.message.from_user.name

    if user_name == ADMIN_USERNAME:
        group_list = ""
        for group in groups:
            group_list += group + " \n"
        await update.message.reply_text(
            f"Hier sind alle Gruppen: \n\n'{group_list}'"
        )

async def admin_delete_groups(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_name = update.message.from_user.name

    if user_name == ADMIN_USERNAME:
        groups = {}
        save_data(GROUPS_FILE, groups)
        await update.message.reply_text(
            f"Alle Gruppen wurden gelöscht."
        )


# Main function to set up the bot
def main() -> None:
    application = Application.builder().token(BOT_TOKEN).build()

    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("create", create_group))
    application.add_handler(CommandHandler("join", join_group))
    application.add_handler(CommandHandler("leave", leave_group))
    application.add_handler(CommandHandler("status", group_status))
    application.add_handler(CommandHandler("set-preference", set_preference))
    application.add_handler(CommandHandler("delete-preference", del_preference))
    application.add_handler(CommandHandler("assign", assign_circle))
    application.add_handler(CommandHandler("showallgroups", admin_show_groups))
    application.add_handler(CommandHandler("deleteallgroups", admin_delete_groups))

    # Start the bot
    application.run_polling()

if __name__ == '__main__':
    main()
