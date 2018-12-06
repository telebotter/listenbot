import subprocess
import random
import yaml
import sys
import time
import logging
import json
import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler
from telegram.ext.filters import Filters
from github import Github
from uuid import uuid4

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
commands = {}
with open('strings.yml', 'r') as f:
    strings = yaml.safe_load(f)
with open('config.yml', 'r') as f:
    config = yaml.safe_load(f)


# ---------------------------------------------------------------------------- #
# ----------------------------- Helper --------------------------------------- #
# ---------------------------------------------------------------------------- #


def reply(update, text):
    update.message.reply_text(text=text, quote=False, pase_mode='Markdown')



def printlist(update, chat_data):
    #TODO: try to update/remove last list
    try:
        list = chat_data['lists'][chat_data['active']]
        buttons = [[InlineKeyboardButton(it, callback_data='removeitem;{}'.format(i))] for i, it in enumerate(list['items'])]
        keyboard = InlineKeyboardMarkup(buttons)
        update.message.reply_text(text=list['name'], reply_markup=keyboard, parse_mode='Markdown', quote=False)
    except Exception as e:
        reply(update, str(e))
# ---------------------------------------------------------------------------- #
# ----------------------------- Commands  ------------------------------------ #
# ---------------------------------------------------------------------------- #

def start(bot, update, user_data, chat_data):
    bot.send_message(chat_id=update.message.chat_id, text=strings['welcome'], quote=False)
commands['start'] = {'desc': "Wilkommensnachricht", 'user_data': True, 'chat_data': True, 'func': start}


def help(bot, update):
    answ = "In arbeit.. " #get_commandlist()
    update.message.reply_text(text=answ, quote=False, parse_mode='Markdown')
commands['help'] = {'desc': strings['help'], 'func': help}


def newlist(bot, update, args, user_data, chat_data):
    "creates a new list with name (args) in chat_data"
    list = {'name': ' '.join(args), 'items': []}
    if not 'lists' in chat_data:
        print('lists not in chat_data make sure it was created sucessfully')
        chat_data['lists'] = {}
    list_id = uuid4()
    chat_data['lists'][list_id] = list
    chat_data['active'] = list_id
commands['newlist'] = {'desc': "erstellt eine neue liste", 'func': newlist, 'args':True, 'chat_data': True, 'user_data': True}


def lists(bot, update, args, user_data, chat_data):
    if not 'lists' in chat_data:
        chat_data['lists'] = []  # replace with "load or create pickle stuff"
    if len(chat_data['lists']) > 0:
        buttons = [ [InlineKeyboardButton(l['name'], callback_data='listmenu;{}'.format(str(i)))]
                for i, l in enumerate(chat_data['lists']) ]
        buttons.append([InlineKeyboardButton('Abbrechen', callback_data='removemessage')])
        keyboard = InlineKeyboardMarkup(buttons)
        update.message.reply_text(text='Wähle eine Liste:',
                reply_markup=keyboard, parse_mode='Markdown', quote=False)
    else:
        print('error')
commands['lists'] = {'desc': "edit lists", 'func': lists, 'args':True, 'chat_data': True, 'user_data': True}


def activate(bot, update, args, chat_data):
    """ activates a list that matches the name excatly or shows a menu
    """
    pass


"""
def setup(bot, update):
    mess = bot.send_message(chat_id=update.message.chat_id, text=' ... ')
    print(mess)
    return
"""

def addtolist(bot, update, user_data, chat_data):
    if not 'lists' in chat_data:
        reply(update, 'keine daten')
    elif len(chat_data['lists']) < 1:
        reply(update, 'Noch keine Listen erstellt')
    else:
        chat_data['lists'][-1]['items'].append(update.message.text)
        printlist(update, chat_data)

# ---------------------------------------------------------------------------- #
# ----------------------------- Admin  --------------------------------------- #
# ---------------------------------------------------------------------------- #

# @restricted
def botsay(bot, update, args):
    answ = ' '.join(args)
    bot.send_message(chat_id=group_id, text=answ, quote=False, parse_mode='Markdown')



# ---------------------------------------------------------------------------- #
# ---------------------------- Callback -------------------------------------- #
# ---------------------------------------------------------------------------- #

def callback(bot, update, user_data, chat_data):
    query = update.callback_query
    data = query.data.split(';')
    if data[0] == 'listmenu':
        listmenu(bot, update, chat_data, data)
    elif data[0] == 'activatelist':
        activatelist(bot, update, chat_data, data)
    elif data[0] == 'renamelist':
        renamelist(bot, update, chat_data, data)
    elif data[0] == 'removemessage':
        update.callback_query.message.delete()
    elif data[0] == 'removeitem':
        chat_data['lists'][-1]


def listmenu(bot, update, chat_data, data):
    """ return menu for a single list
    """
    list = chat_data['lists'][int(data[1])]
    text = "*{}* bearbeiten:".format(list['name'])
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton('Aktivieren', callback_data='activatelist;{}'.format(data[1]))],
        [InlineKeyboardButton('Umbenennen', callback_data='renamelist;{}'.format(data[1]))],
        [InlineKeyboardButton('Löschen', callback_data='removelist;{}'.format(data[1]))],
        [InlineKeyboardButton('Abbrechen', callback_data='removemessage')],
    ])
    update.callback_query.message.edit_text(text=text, parse_mode='Markdown')
    update.callback_query.message.edit_reply_markup(reply_markup=keyboard)
    #index = int(data[2])
    if data[2] == 'activate':
        editlist_activate(bot, update, chat_data, data)
    elif data[2] == 'rename':
        renamelist(bot, update, chat_data, data)

def activatelist(bot, update, chat_data, data):
    index = int(data[1])
    chat_data['lists'].append(chat_data['lists'].pop(index))
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Ok', callback_data='removemessage')]])
    update.callback_query.message.edit_text(text='*{}* is now activ.'.format(chat_data['lists'][-1]['name'], reply_markup=keyboard, parse_mode='Markdown'))
    #update.callback_query.message.edit_reply_markup(reply_markup=None)

def renamelist(bot, update, chat_data, data):
    print('renaming')
    reply(update, 'Noch in arbeit...')

# ---------------------------------------------------------------------------- #
# ---------------------------- Main ------------------------------------------ #
# ---------------------------------------------------------------------------- #

if __name__ == '__main__':

    with open('config.yml', 'r') as cf:
        config = yaml.safe_load(cf)
    with open('strings.yml', 'r') as sf:
        strings = yaml.safe_load(sf)

    updater = Updater(token=config['token'])
    dispatcher = updater.dispatcher
    callback_handler = telegram.ext.CallbackQueryHandler(callback, pass_chat_data=True, pass_user_data=True)
    dispatcher.add_handler(callback_handler)
    handlers = {}
    for c in commands:
        cmd = commands[c]
        handler = CommandHandler(c, cmd['func'],
                                            pass_args=cmd.get('args', False),
                                            pass_user_data=cmd.get('user_data', False),
                                            pass_chat_data=cmd.get('chat_data', False))
        dispatcher.add_handler(handler)
    message_handler = MessageHandler((Filters.text & (~Filters.command)), addtolist, pass_user_data=True, pass_chat_data=True)
    dispatcher.add_handler(message_handler)
    # hidden cmds
    #botsay_handler = CommandHandler('botsay', botsay, pass_args=True)
    #dispatcher.add_handler(botsay_handler)
    updater.start_polling()
