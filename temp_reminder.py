#!/usr/bin/env python
# -*- coding: utf-8 -*-

from telegram.ext import Updater, CommandHandler, \
    MessageHandler, Filters
import datetime

bot_token = "$TOKEN"

days = ['ALL', 'WD', 'WE', 'M', 'T', 'W', 'R', 'F', 'S', 'N']
days_dict = {
    'M': 0,
    'T': 1,
    'W': 2,
    'R': 3,
    'F': 4,
    'S': 5,
    'N': 6,
}

num_dict = {
    '0': 'M',
    '1': 'T',
    '2': 'W',
    '3': 'R',
    '4': 'F',
    '5': 'S',
    '6': 'N',
}

error_output = ''
error_msg = {
    "invalid_time":     "Please check your input. \n\n" \
                        + "Time should be in 24h format (HHMM).",
    "invalid_day":      "Please check your input. \n\n" \
                        + "Use 'R' for Thur and 'N' for Sun. \n\n" \
                        + "E.g. 'All' - everyday; 'WD' - weekdays; " \
                        + "'WE' - weekends; 'MWF' - Mon, Wed & Fri",
    "invalid_format":   "Please check your format again.", 
    "invalid_command":  "Please enter a valid command."
}

start_msg = "Use this bot to set reminders. \n\n" \
    + "/set - set new reminder \n" \
    + "/view - view your reminders \n" \
    + "/delete - delete reminders"

set_msg = "Setting a new reminder... \n\n" \
    + "Please input the day(s), time and reminder message in the following format: \n\n" \
    + "DAY(S), TIME, MESSAGE \n\n" \
    + "For DAY(S): \n "\
    + "\t- All: Everyday \n"\
    + "\t- WD: Weekdays \n"\
    + "\t- WE: Weekends \n"\
    + "\t- Use 'R' for Thu and 'N' for Sun \n"\
    + "E.G. Enter MRN, 1500, Take temperature to set reminder for  Mon, Thu & Sun \n\n" \
    + "/cancel to exit"

del_msg = "Which reminder do you want to remove? \n" \
    + "Enter a number. \n" \
    + "/cancel to exit \n"


def convert_days(day_tup):
    result = ''
    if len(day_tup) == 7:
        return "ALL"
    elif day_tup == (5, 6):
        return "WE"
    elif day_tup == tuple(list(range(5))):
        return "WD"
    else:
        for day_num in day_tup:
            result += num_dict[str(day_num)]
        return result


def revert_input(rem_dict):
    return f""" \
        {convert_days(rem_dict['days'])}, {rem_dict['time'].strftime("%H%M")}, \
{rem_dict['msg']}""".strip() + "\n"


def valid_days(day_list):
    day_list = day_list.strip().upper()
    if day_list in days[0:3]:
        return True
    else:
        result = False not in [day in days for day in day_list]
        return result


def valid_time(time):
    time = time.strip()
    try:
        hour = int(time[0] + time[1])
        minute = int(time[2] + time[3])
    except:
        return False

    if len(time) == 4 \
        and 0 <= hour <= 24 \
        and 0 <= minute <= 59:
        return True 
    else:
        return False
        

def valid_response(user_input):
    global error_output 

    user_input = user_input.split(',')
    if not len(user_input) == 3:
        error_output = error_msg['invalid_format']
        return False
    elif not valid_days(user_input[0]):
        error_output = error_msg['invalid_day']
        return False
    elif not valid_time(user_input[1]):
        error_output = error_msg['invalid_time']
        return False
    else:
        return True
       

def send_reminder(context):
    chat_data = context.job.context.chat_data
    user_data = context.job.context.user_data
    msg = "[REMINDER] " + user_data['latest_reminder']['msg']
    #  print(msg)
    context.bot.send_message(chat_data['chat_id'], text=msg)


def update_reminder_list(new_reminder, user_data):
    #  print("new " + new_reminder)
    new_reminder = new_reminder.split(',')
    input_days = new_reminder[0].upper()
    input_time = new_reminder[1].strip()
    input_msg = new_reminder[2].strip()

    reminder_days = ()

    if input_days == "ALL":
        reminder_days = tuple([i for i in range(7)])
    elif input_days == "WD":
        reminder_days = tuple([i for i in range(5)])
    elif input_days == "WE":
        reminder_days = (5, 6)
    else:
        for day in input_days:
            reminder_days += (days_dict[day],)

    reminder_time = datetime.time.fromisoformat(input_time[0:2] + ':' \
        + input_time[2:] + "+08:00")

    reminder = {
        'days': reminder_days, 
        'time': reminder_time,
        'msg': input_msg
    }

    return reminder
    

def readback_last_reminder(user_data):
    if 'latest_reminder' in user_data:
        #  print(user_data['latest_reminder'])
        return revert_input(user_data['latest_reminder'])
    return "No reminders."


def handle_input(update, context):
    chat_id = update.effective_chat.id
    user_input = update.message.text
    chat_data = context.chat_data
    chat_data['chat_id'] = chat_id
    user_data = context.user_data
    #  print(chat_data['state'])
    #  print(type( user_data))

    if chat_data['state'] == 1:
        if valid_response(user_input):
            #  print("valid input") 
            
            new_reminder = update_reminder_list(user_input, user_data)
            user_data['latest_reminder'] = new_reminder
            #  print(user_data)

            #  print(context.user_data)
            new_job = context.job_queue.run_daily(
                send_reminder, 
                user_data['latest_reminder']['time'], 
                user_data['latest_reminder']['days'],
                context=context,
            )
            user_data['latest_reminder']['job'] = new_job
            
            if 'reminder_list' not in user_data:
                user_data['reminder_list'] = []
            user_data['reminder_list'].append(user_data['latest_reminder'])
            
            context.bot.send_message(chat_id, text="Success!")
            readback_msg = "Reminder set for:\n " + readback_last_reminder(user_data)
            context.bot.send_message(chat_id, text=readback_msg)
            chat_data['state'] = 0
        else:
            context.bot.send_message(chat_id, text=error_output)
    elif chat_data['state'] == 2:
        index = int(user_input) - 1
        if 0 <= index < len(user_data['reminder_list']):
            chat_data['state'] = 3
            chat_data['index_to_remove'] = index
            context.bot.send_message(chat_id, text="Are you sure? Y/N")
        else:
            context.bot.send_message(chat_id, text="Invalid number.\n\n /cancel to exit.")
    elif chat_data['state'] == 3:
        if user_input.upper() == 'Y':
            index = chat_data['index_to_remove']
            del chat_data['index_to_remove']
            job = user_data['reminder_list'][index]['job']
            job.schedule_removal()
            del user_data['reminder_list'][index]
            context.bot.send_message(chat_id, text=f"Reminder {index+1} removed.")
        else:
            context.bot.send_message(chat_id, text="Aborted.")
        chat_data['state'] = 0
        
    #  print(user_input)
    #  return user_input


def start(update, context):
    chat_id = update.effective_chat.id
    chat_data = context.chat_data
    chat_data['chat_id'] = chat_id
    chat_data['state'] = 0
    context.bot.send_message(chat_id, text=start_msg)


def set_reminder(update, context):
    chat_id = update.effective_chat.id
    chat_data = context.chat_data
    chat_data['state'] = 1
    context.bot.send_message(chat_id, text=set_msg)
    
    
def cancel(update, context):
    chat_id = update.effective_chat.id
    chat_data = context.chat_data
    chat_data['state'] = 0
    context.bot.send_message(chat_id, text=start_msg)


def view(update, context):
    chat_id = update.effective_chat.id
    chat_data = context.chat_data
    user_data = context.user_data 
    curr_reminders = ''
    
    if 'reminder_list' in user_data:
        for i, reminder in enumerate(user_data['reminder_list']):
            #  print(revert_input(reminder))
            curr_reminders += f"""
                {i+1} - {revert_input(reminder)}""".strip() + '\n'
    view_msg = f"""
        Your current reminders:
            {curr_reminders}

        /delete - to delete reminders
    """.strip()
    context.bot.send_message(chat_id, text=view_msg)


def delete(update, context):
    chat_id = update.effective_chat.id
    chat_data = context.chat_data
    chat_data['state'] = 2
    context.bot.send_message(chat_id, text=del_msg)

        
def unknown_cmd(update, context):
    chat_id = update.effective_chat.id
    context.bot.send_message(chat_id, text=error_msg["invalid_command"])


def main():
    print("Reminder bot running...")
    updater = Updater(bot_token, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start",start))
    dp.add_handler(CommandHandler("set", set_reminder))
    dp.add_handler(CommandHandler("cancel", cancel))
    dp.add_handler(CommandHandler("view", view))
    dp.add_handler(CommandHandler("delete", delete))
    dp.add_handler(MessageHandler(Filters.command, unknown_cmd))
    dp.add_handler(MessageHandler(Filters.text, handle_input))
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
