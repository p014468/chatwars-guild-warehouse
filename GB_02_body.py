#import logging
#import requests
#import json
#import re
import os
import sqlite3
from config_guildbot import TOKEN, ADMIN_ID, chatwars_id, chatwars_username, DIR, db_file
from sqlite3 import Error
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler
from emoji import emojize

welcome_text = '''Please forward me your warehouse from ''' + '''@''' + chatwars_username + ''' in following order: 
<a href=\'https://t.me/share/url?url=/g_stock_res\'>/g_stock_res</a>
<a href=\'https://t.me/share/url?url=/g_stock_alch\'>/g_stock_alch</a>
<a href=\'https://t.me/share/url?url=/g_stock_misc\'>/g_stock_misc</a>
<a href=\'https://t.me/share/url?url=/g_stock_rec\'>/g_stock_rec</a>
<a href=\'https://t.me/share/url?url=/g_stock_parts\'>/g_stock_parts</a>
<a href=\'https://t.me/share/url?url=/g_stock_other\'>/g_stock_other</a>'''
#logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

CHOOSE_MSTOCK, FILL_MSTOCK = range(2)
CHOOSE_MSTOCK_SHOW = range(1)
CHOOSE_MSTOCK_DELETE = range(1)
stockType = ''

updater = Updater(token=TOKEN, use_context = True)
dispatcher = updater.dispatcher

res = emojize(':package:', use_aliases=True)
alch = emojize(':alembic:', use_aliases=True)
misc = emojize(':card_file_box:', use_aliases=True)
rec = emojize(':page_with_curl:', use_aliases=True)

# -- begin service functions --

def isAdmin(id):
    return id == ADMIN_ID

def create_connection(db_file):
    return sqlite3.connect(db_file)

def insert_into(conn, value_tuple, stockType, isTemp=False):
    c = conn.cursor()
    if isTemp:
        sql = 'insert into g_temp (user_id, res_id, res_name, amount) values (?,?,?,?)'
    elif len(value_tuple) == 2 and not isTemp:
        sql = 'insert into g_stock_' + stockType + '_m (res_id, res_name) values (?,?)'
    elif len(value_tuple) == 4:
        sql = 'insert into g_stock_' + stockType + ' (user_id, res_id, res_name, amount) values (?,?,?,?)'
    else:
        return -1
    try:
        c.execute(sql, value_tuple)
        #print('Row is inserted')
        conn.commit()
    except Error as e1:
        print(e1)
    return 1

def select_from_master(conn, stockType):
    ''' 
    get all row values from a stockType master table
    - stockType is in res, alch, misc, rec, parts, other
    - returns a list of tuples with 0th element as code and 1st element as name in a tuple
    '''
    c = conn.cursor()
    sql = 'select res_id, res_name from g_stock_' + stockType + '_m'
    try:
        c.execute(sql)
        rows = c.fetchall()
    except Error as e1:
        print(e1)
    return rows

def delete_from_master(conn, stockType):
    c = conn.cursor()
    sql = 'delete from g_stock_' + stockType + '_m'
    try:
        c.execute(sql)
        print('Rows are deleted.')
        conn.commit()
    except Error as e1:
        print(e1)

def select_from_stock(conn, stockType):
    ''' 
    get all row values from a stockType table
    - stockType is in res, alch, misc, rec, parts, other
    - returns a list of tuples with 0th element as user_id 1st as res code, 2nd as name, 3rd as amount in a tuple
    '''
    c = conn.cursor()
    sql = 'select user_id, res_id, res_name, amount from g_stock_' + stockType
    try:
        c.execute(sql)
        rows = c.fetchall()
    except Error as e1:
        print(e1)
    return rows

def delete_from_stock(conn, stockType, isTemp=False):
    c = conn.cursor()
    if isTemp:
        stockType = ''
        c.execute('delete from g_temp')
        print('Temp table is now empty.')
        conn.commit()
    else:
        c.execute('delete from g_stock_' + stockType)
        print('The ' + stockType + ' table is now empty.')
        conn.commit()


# -- end service functions 

def unknown(update, context):
    context.bot.send_message(update.effective_chat.id, '¯\\_(ツ)_/¯')

def start(update, context):
    if os.path.exists(DIR + str(update.message.from_user.id)):
        context.bot.send_message(update.effective_chat.id, 'Hi again.')
    else:
        context.bot.send_message(update.effective_chat.id, 'Hello. I don\'t know you.')
        context.bot.send_message(update.effective_chat.id, welcome_text, parse_mode = 'HTML')
        os.mkdir(DIR + str(update.message.from_user.id))

def set_master_stock(update, context): # in conversation hanlder set_master_stock this would be an entry_point
    reply_keyboard = [[res + 'Resources', alch + 'Alchemy', misc + 'Misc'],[rec + 'Recipes', 'Parts', 'Other']]
    chat_id = update.effective_chat.id
    if not isAdmin(chat_id):
        unknown(update, context)
        return ConversationHandler.END
    else:
        text = 'Choose a stock type you want to configure. If you are want to cancel the task, type /finish.'
        context.bot.send_message(
            chat_id, 
            text, 
            reply_markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=True)
        )
    return CHOOSE_MSTOCK

def choose_master_stock(update, context):
    global stockType
    chat_id = update.effective_chat.id
    chat_message = update.message.text
    if not isAdmin(chat_id):
        context.bot.send_message(chat_id, '¯\\_(ツ)_/¯')
        return ConversationHandler.END
    else:
        if chat_message == 'Other' or chat_message == 'Parts':
            stockType = chat_message.lower()
        elif chat_message == res + 'Resources' or chat_message == rec + 'Recipes':
            stockType = chat_message[1:4].lower()
        elif chat_message == alch + 'Alchemy' or chat_message == misc + 'Misc':
            stockType = chat_message[1:5].lower()
        else:
            context.bot.send_message(chat_id, 'Wrong stock type.')
            return ConversationHandler.END
        text = 'You chose the \'' + stockType + '\' stock type. Send the items list in the following format: Code Name, e.g. 01 Thread'
        context.bot.send_message(chat_id, text, reply_markup = ReplyKeyboardRemove())
        return FILL_MSTOCK


def fill_master_stock(update, context):
    chat_id = update.effective_chat.id
    chat_message = update.message.text
    if not isAdmin(chat_id):
        context.bot.send_message(chat_id, '¯\\_(ツ)_/¯')
        return ConversationHandler.END
    else:
        conn = create_connection(db_file)
        masterStockLines = chat_message.splitlines() # we get ['01 Thread', '02 Stick', '03 Pelt'...]
        for i in range(len(masterStockLines)):
            res_id = masterStockLines[i][0:masterStockLines[i].find(' ')] # '01' = cut the i-then element from 0 to first space
            res_name = masterStockLines[i][masterStockLines[i].find(' ')+1:] # 'Thread' = cut the i-the element from first space until end of string
            row = (res_id, res_name)
            result = insert_into(conn, row, stockType)

        context.bot.send_message(chat_id, 'Master table \'' + stockType + '\' is filled with your values.')
    return ConversationHandler.END # if no return of ConversationHandler.END then it will take as input every next message for insert into master table

def finish(update, context):
    chat_id = update.effective_chat.id
    if not isAdmin(chat_id):
        unknown(update, context)
        return ConversationHandler.END
    else:
        context.bot.send_message(chat_id, 'To restart setting the master stock, press /set_master_stock', reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

def get_master_stock(update, context): # entry_point in ConverstaionHandler get_master_stock
    reply_keyboard = [[res + 'Resources', alch + 'Alchemy', misc + 'Misc'],[rec + 'Recipes', 'Parts', 'Other']]
    chat_id = update.effective_chat.id
    if not isAdmin(chat_id):
        unknown(update, context)
        return ConversationHandler.END
    else:
        text = 'Choose a master stock type you want to see.'
        context.bot.send_message(chat_id, text, reply_markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=True))
    return CHOOSE_MSTOCK_SHOW

def show_master_stock(update, context):
    chat_id = update.effective_chat.id
    chat_message = update.message.text
    if not isAdmin(chat_id):
        context.bot.send_message(chat_id, '¯\\_(ツ)_/¯')
        return ConversationHandler.END
    else:
        if chat_message == 'Other' or chat_message == 'Parts':
            stockType = chat_message.lower()
        elif chat_message == res + 'Resources' or chat_message == rec + 'Recipes':
            stockType = chat_message[1:4].lower()
        elif chat_message == alch + 'Alchemy' or chat_message == misc + 'Misc':
            stockType = chat_message[1:5].lower()
        else:
            context.bot.send_message(chat_id, 'Wrong stock type.')
            return ConversationHandler.END
        conn = create_connection(db_file)
        rows = select_from_master(conn, stockType) # save returned list of tuples into variable rows: [('01', 'Thread'), ('02', 'Stick')] etc.
        text = '<b>Id Name</b>\n'
        if len(rows) == 0:
            text = 'This master stock is empty.'
            context.bot.send_message(chat_id, text, reply_markup=ReplyKeyboardRemove())
            return ConversationHandler.END
        else:
            for i in range(len(rows)):
                text = text + rows[i][0] + ' ' + rows[i][1] + '\n'
            context.bot.send_message(chat_id, text, parse_mode = 'HTML', reply_markup=ReplyKeyboardRemove())
    
    return ConversationHandler.END

def del_master_stock(update, context): # entry_point in ConverstaionHandler del_master_stock
    reply_keyboard = [[res + 'Resources', alch + 'Alchemy', misc + 'Misc'],[rec + 'Recipes', 'Parts', 'Other']]
    chat_id = update.effective_chat.id
    if not isAdmin(chat_id):
        unknown(update, context)
        return ConversationHandler.END
    else:
        text = 'Choose a master stock type you want to delete.'
        context.bot.send_message(chat_id, text, reply_markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=True))
    return CHOOSE_MSTOCK_DELETE

def choose_del_master_stock(update, context):
    chat_id = update.effective_chat.id
    chat_message = update.message.text
    if not isAdmin(chat_id):
        context.bot.send_message(chat_id, '¯\\_(ツ)_/¯')
        return ConversationHandler.END
    else:
        if chat_message == 'Other' or chat_message == 'Parts':
            stockType = chat_message.lower()
        elif chat_message == res + 'Resources' or chat_message == rec + 'Recipes':
            stockType = chat_message[1:4].lower()
        elif chat_message == alch + 'Alchemy' or chat_message == misc + 'Misc':
            stockType = chat_message[1:5].lower()
        else:
            context.bot.send_message(chat_id, 'Wrong stock type.')
            return ConversationHandler.END
        conn = create_connection(db_file)
        delete_from_master(conn, stockType)
        text = 'Rows are deleted.'
        context.bot.send_message(chat_id, text, reply_markup=ReplyKeyboardRemove())
    
    return ConversationHandler.END

def getStockLinesTuplesList(user_id, guildStockRaw): # guildStockRaw is a raw input from chatwars guild warehouse
    stockLines = guildStockRaw[17:].splitlines() # get rid of 'Guild Warehouse:\n' 
    stockLinesTuplesList = [] # create an empty list to save the rows into
    for i in range(len(stockLines)):
        id_name, amount = stockLines[i].split(' x ') # split into '01 Thread' and '500' from '01 Thread x 500'
        res_id = id_name[0:id_name.find(' ')] # search for a first whitespace and cut until it: 35 Crafted leather --> 35
        res_name = id_name[id_name.find(' ')+1:] # cut from first whitespace until end of string
        amount = int(amount)
        row = (user_id, res_id, res_name, amount)
        stockLinesTuplesList.append(row)
    return stockLinesTuplesList # return a list of tuples like [(12345, '01', 'Thread', 500), (12345, '02', 'Stick', 200)]

# define stock type
def getStockType(conn, stockLinesTuplesList):
    stockType = ''
    if stockLinesTuplesList[0][1][:1] == 'r':  # get the very first row ...[0] then the second element of tuple ...[0][1] then the first letter ...[0][1][:1]
        return 'rec'
    elif stockLinesTuplesList[0][1][:1] == 'k':
        return 'parts'
    elif stockLinesTuplesList[0][1][:1] == 'a' or stockLinesTuplesList[0][1][:1] == 'w' or stockLinesTuplesList[0][1][:1] == 'u':
        return 'other'
    else:
        c = conn.cursor()
        delete_from_stock(conn, stockType, isTemp=True) # cleaning temp table before writing values into it
        for i in range(len(stockLinesTuplesList)):
            insert_into(conn, stockLinesTuplesList[i], stockType, isTemp=True)
        stockType = ['res', 'alch', 'misc']
        for i in range(len(stockType)):
            c.execute('select count(a.res_id) from g_temp a inner join g_stock_' + stockType[i] + '_m b on a.res_id = b.res_id')
            y = c.fetchone()[0]
            if y != 0:
                return stockType[i]


def msg(update, context): 
    chat_id = update.effective_chat.id
    message = update.message.text
    if update.message.forward_from != None and update.message.forward_from.id == chatwars_id and update.message.forward_from.username == chatwars_username:
        conn = create_connection(db_file)
        stockLinesTuplesList = getStockLinesTuplesList(chat_id, message)
        stockType = getStockType(conn, stockLinesTuplesList)
        for i in range(len(stockLinesTuplesList)):
            insert_into(conn, stockLinesTuplesList[i], stockType)
        context.bot.send_message(chat_id, 'The <b>' + stockType + '</b> table was filled with your values. To get the difference, please send the guild stock again', parse_mode='HTML')
    else:
        text = 'It doesn\'t seem to be a correct warehouse data. ' + welcome_text
    context.bot.send_message(chat_id, text, parse_mode = 'HTML')
    
start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)

# handlers for setting master stock
set_master_stock_handler = CommandHandler('set_master_stock', set_master_stock)
choose_master_stock_handler = MessageHandler(Filters.text, choose_master_stock)
fill_master_stock_handler = MessageHandler(Filters.text, fill_master_stock)

# handlers for getting master stock
get_master_stock_handler = CommandHandler('get_master_stock', get_master_stock)
show_master_stock_handler = MessageHandler(Filters.text, show_master_stock)

# handlers for deleting master stock
del_master_stock_handler = CommandHandler('del_master_stock', del_master_stock)
choose_del_master_stock_handler = MessageHandler(Filters.text, choose_del_master_stock)

# handler for stopping setting/getting/deleting master stock
finish_handler = CommandHandler('finish', finish)

# conversation for setting master stock
set_master_stock_conv_handler = ConversationHandler(
    entry_points=[set_master_stock_handler], 
    states={
        CHOOSE_MSTOCK: [choose_master_stock_handler],
        FILL_MSTOCK: [fill_master_stock_handler]
    },
    fallbacks=[finish_handler]
    )
dispatcher.add_handler(set_master_stock_conv_handler)

# conversation for getting master stock
get_master_stock_conv_handler = ConversationHandler(
    entry_points=[get_master_stock_handler],
    states={
        CHOOSE_MSTOCK_SHOW: [show_master_stock_handler]
    },
    fallbacks=[finish_handler]
)
dispatcher.add_handler(get_master_stock_conv_handler)

# conversation for deleting master stock
del_master_stock_conv_handler = ConversationHandler(
    entry_points=[del_master_stock_handler],
    states={
        CHOOSE_MSTOCK_DELETE: [choose_del_master_stock_handler]
    },
    fallbacks=[finish_handler]
)
dispatcher.add_handler(del_master_stock_conv_handler)

msg_handler = MessageHandler(Filters.text, msg)
dispatcher.add_handler(msg_handler)

unknown_handler = MessageHandler(Filters.command, unknown)
dispatcher.add_handler(unknown_handler)

def main():
	updater.start_polling()

    #updater.idle()

if __name__ == '__main__':
    main()
