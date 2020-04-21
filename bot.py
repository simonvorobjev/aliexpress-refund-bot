token = "YOURBOTTOKEN"

import telegram
import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackQueryHandler
from telegram.ext.dispatcher import run_async
import threading, queue
import AliExpress
import sys
import os
import datetime
import sqlite3
import epn_parse

CHAT_LINK = 'https://t.me/ChatAliexpressRefunderBot'
WELCOME_TEXT = 'Дорогие друзья! 👋 Число вопрос по поводу бота растет 📈, и я вижу что не всем хочется писать в личку ✍️, поэтому я хочу предложить вам новый способ задать вопросы по боту 📞, товарам 🛒, поиску 🔍, рефанду 💰 и другим темам! Присоединяйтесь к чату 📝 бота @AliexpressRefunderBot! Здесь я отвечу на ваши вопросы ❓, услышу ваши пожелания 💬 и улучшу бота 🛠, получу ваш фидбек ♥️ и многое другое! Жду вас в чате!\n\n      [Зайти в чат!](' + CHAT_LINK + ')\n\nВведите модель товара для поиска (например "клавиатура Motospeed"):'
TIMEOUT = 400
CASHBACK_LINK = 'https://givingassistant.org/?rid=1vT1QGCSmU'
MY_ID = 275413429

vape_filters = 'vs <бренд>,for <бренд>,atomiz,part,case,cover,replac,pcs'
phone_filters = 'case,cover,glass,for <бренд>,vs <бренд>,pcs,replac,motherboard,part'
laptop_filters = 'case,cover,part,replac,motherboard,assembl,glass,bag,pcs'

#conn = sqlite3.connect("mydatabase.db")
#cursor = conn.cursor()
#cursor.execute("""CREATE TABLE users
#                  (user_id text primary key, user_name text, last_login text,
#                   total_logins text)
#               """)
#conn.commit()
#conn.close()

updater = Updater(token=token, workers=50)

PRODUCT_CHOOSE, BRAND_CHOOSE, PRICE_RANGE_CHOOSE, FILTER_WORDS_CHOOSE, SEARCH_NEXT = range(5)
GET_MESSAGE_TO_POST = range(1)
GET_MESSAGE_TO_PRINT = range(1)
CHOOSE_FILTERS = range(1)
condition_result_ready_dict = {}
condition_user_ready_dict = {}
link_dict = {}
cookie_list = []
reply_keyboard = [['/find', '/test'],
                  ['/start', '/help'],
                  ['/filters', '/cancel']]
markup = telegram.ReplyKeyboardMarkup(reply_keyboard)


def update_db(update):
    user_id = str(update.message.chat_id)
    user_name = update.message.from_user.username
    last_login = datetime.datetime.now().strftime("%I:%M%p on %B %d, %Y")
    total_logins = str(1)
    if not os.path.exists("mydatabase.db"):
        conn = sqlite3.connect("mydatabase.db")
        cursor = conn.cursor()
        cursor.execute("""CREATE TABLE users
                  (user_id text primary key, user_name text, last_login text,
                   total_logins text)
               """)
        conn.commit()
        conn.close()
    conn = sqlite3.connect("mydatabase.db")
    cursor = conn.cursor()
    count = cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,)).fetchall()
    if len(count) > 0:
        total_logins = str(int(count[0][3]) + 1)
    conn.execute("INSERT OR REPLACE INTO users values (?, ?, ?, ?)", (user_id, user_name, last_login, total_logins))
    conn.commit()
    cursor.close()
    conn.close()


def get_all_users_from_db():
    conn = sqlite3.connect("mydatabase.db")
    cursor = conn.cursor()
    all_users = cursor.execute("SELECT * FROM users").fetchall()
    cursor.close()
    conn.close()
    return all_users


def delete_user_from_db(user_id):
    conn = sqlite3.connect("mydatabase.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE user_id=?", (user_id,))
    conn.commit()
    cursor.close()
    conn.close()


def start(bot, update):
    update_db(update)
    bot.send_message(chat_id=update.message.chat_id, reply_markup=markup, text='Бот ищет товары с неправильным брендом, который можно перевести в подделку и получить 100% рефанд!' 
                                                          'Чтобы искать товар, введите поиск, как вы искали бы его на Aliexpress. '
                                                          'Например, вводить просто "телефон" бессмысленно, нужно вводить, например '
                                                          '"телефон Ulefone S7". Искать самые популярные бренды вроде "телефон Xiaomi" '
                                                          'так же бессмысленно, так как их продавцов мало, они авторизованные, '
                                                          'и заполняют поле "бренд" в описании правильно. Идеальный поиск - '
                                                          'ввести что-то содержащее имя бренда, имя модели и тип товара, например '
                                                          '"Meizu EP51 Wireless Bluetooth Earphone".'
                                                          ' По всем вопросам обращайтесь к @simonvorobyov (https://t.me/simonvorobyov)')


def help(bot, update):
    update_db(update)
    bot.send_message(chat_id=update.message.chat_id, reply_markup=markup, text='Бот ищет товары с неправильным брендом, который можно перевести в подделку и получить 100% рефанд!'
                                                          'Чтобы искать товар, введите поиск, как вы искали бы его на Aliexpress. '
                                                          'Например, вводить просто "телефон" бессмысленно, нужно вводить, например '
                                                          '"телефон Ulefone S7". Искать самые популярные бренды вроде "телефон Xiaomi" '
                                                          'так же бессмысленно, так как их продавцов мало, они авторизованные, '
                                                          'и заполняют поле "бренд" в описании правильно. Идеальный поиск - '
                                                          'ввести что-то содержащее имя бренда, имя модели и тип товара, например '
                                                          '"Meizu EP51 Wireless Bluetooth Earphone".'
                                                          ' По всем вопросам обращайтесь к @simonvorobyov (https://t.me/simonvorobyov)')


@run_async
def iddqd(bot, update):
        bot.send_message(chat_id=update.message.chat_id, text="Secret found! Stopping server!")
        global updater
        updater.stop()
        sys.exit(0)


@run_async
def idfa(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text="Secret found! Restarting server!")
    global updater
    updater.stop()
    os.execl(sys.executable, 'python3', 'bot.py', *sys.argv[1:])


def text_reply(bot, update, user_data):
    bot.send_message(chat_id=update.message.chat_id, text="Введите /find чтобы начать поиск товара для refund'а."
                                                          " По всем вопросам обращайтесь к @simonvorobyov (https://t.me/simonvorobyov)")


@run_async
def test_search(bot, update, user_data):
    user_data['product'] = 'test'
    user_data['min_price'] = ''
    user_data['max_price'] = ''
    user_data['filter_words'] = []
    user_data['brand'] = ['test']
    update.message.reply_text('Выполняем тестовый запрос!')
    link_dict[update.message.chat_id] = []
    condition_result_ready_dict[update.message.chat_id] = threading.Condition()
    condition_user_ready_dict[update.message.chat_id] = threading.Condition()
    threading.Thread(name='refund_thread',
                     target=AliExpress.find_refund,
                     args=(
                         user_data, link_dict[update.message.chat_id],
                         condition_result_ready_dict[update.message.chat_id],
                         condition_user_ready_dict[update.message.chat_id])).start()
    with condition_result_ready_dict[update.message.chat_id]:
        if not condition_result_ready_dict[update.message.chat_id].wait(TIMEOUT):
            keyboard = [[telegram.InlineKeyboardButton("Find", callback_data='find')],
                        [telegram.InlineKeyboardButton("Repeat", callback_data='repeat')]]
            reply_markup = telegram.InlineKeyboardMarkup(keyboard)
            update.message.reply_text('Поиск завершен по таймауту. /find чтобы начать новый поиск.',
                                      reply_markup=reply_markup, parse_mode=telegram.ParseMode.MARKDOWN)
            return ConversationHandler.END
    if link_dict[update.message.chat_id][0] is None:
        keyboard = [[telegram.InlineKeyboardButton("Find", callback_data='find')],
                    [telegram.InlineKeyboardButton("Repeat", callback_data='repeat')]]
        reply_markup = telegram.InlineKeyboardMarkup(keyboard)
        update.message.reply_text(
            'Больше ничего не найдено, поиск завершен. /find чтобы начать новый поиск, /repeat чтобы повторить последний поиск.',
            reply_markup=reply_markup, parse_mode=telegram.ParseMode.MARKDOWN)
        return ConversationHandler.END
    elif link_dict[update.message.chat_id][0][0] == -1:
        keyboard = [[telegram.InlineKeyboardButton("Find", callback_data='find')],
                    [telegram.InlineKeyboardButton("Repeat", callback_data='repeat')]]
        reply_markup = telegram.InlineKeyboardMarkup(keyboard)
        update.message.reply_text(
            'Не получилось обойти капчу, попробуйте повторить запрос еще раз позже.',
            reply_markup=reply_markup, parse_mode=telegram.ParseMode.MARKDOWN)
        return ConversationHandler.END
    else:
        link = epn_parse.get_cashback_link(cookie_list, link_dict[update.message.chat_id][0][0])
        if link:
            bot.send_message(parse_mode=telegram.ParseMode.MARKDOWN, chat_id=update.message.chat_id,
                             text="Неправильный бренд, бренд товара " + link_dict[update.message.chat_id][0][1] +
                                  " не совпадает с брендами " + str(user_data['brand']) + "\n[!](" +
                                  link_dict[update.message.chat_id][
                                      0][0] + ")[Нажми на ссылку чтобы заказать!](" + link + ")")
        else:
            bot.send_message(parse_mode=telegram.ParseMode.MARKDOWN, chat_id=update.message.chat_id,
                             text="Неправильный бренд, бренд товара " + link_dict[update.message.chat_id][0][1] +
                                  " не совпадает с брендами " + str(user_data['brand']) +
                                  "\n[Нажми на ссылку чтобы заказать!](" + link_dict[update.message.chat_id][0][
                                      0] + ")")
        keyboard = [[telegram.InlineKeyboardButton("Да", callback_data='да'),
                     telegram.InlineKeyboardButton("Нет", callback_data='нет')]]
        reply_markup = telegram.InlineKeyboardMarkup(keyboard)
        update.message.reply_text('Искать дальше? Да/Нет (д/н либо /yes или /no)', reply_markup=reply_markup)
        return SEARCH_NEXT


@run_async
def repeat(bot, update, user_data):
    if ('product' not in user_data) or ('brand' not in user_data):
        keyboard = [[telegram.InlineKeyboardButton("Find", callback_data='find')]]
        reply_markup = telegram.InlineKeyboardMarkup(keyboard)
        update.message.reply_text('В предыдущем поиске не задан бренд или поиск. /find чтобы начать новый поиск.',
                                  reply_markup=reply_markup, parse_mode=telegram.ParseMode.MARKDOWN)
        return ConversationHandler.END
    update.message.reply_text('Повторяем предыдущий поиск!')
    link_dict[update.message.chat_id] = []
    condition_result_ready_dict[update.message.chat_id] = threading.Condition()
    condition_user_ready_dict[update.message.chat_id] = threading.Condition()
    threading.Thread(name='refund_thread',
                     target=AliExpress.find_refund,
                     args=(
                     user_data, link_dict[update.message.chat_id], condition_result_ready_dict[update.message.chat_id],
                     condition_user_ready_dict[update.message.chat_id])).start()
    with condition_result_ready_dict[update.message.chat_id]:
        if not condition_result_ready_dict[update.message.chat_id].wait(TIMEOUT):
            keyboard = [[telegram.InlineKeyboardButton("Find", callback_data='find')],
                        [telegram.InlineKeyboardButton("Repeat", callback_data='repeat')]]
            reply_markup = telegram.InlineKeyboardMarkup(keyboard)
            update.message.reply_text('Поиск завершен по таймауту. /find чтобы начать новый поиск.',
                                      reply_markup=reply_markup, parse_mode=telegram.ParseMode.MARKDOWN)
            return ConversationHandler.END
    if link_dict[update.message.chat_id][0] is None:
        keyboard = [[telegram.InlineKeyboardButton("Find", callback_data='find')],
                    [telegram.InlineKeyboardButton("Repeat", callback_data='repeat')]]
        reply_markup = telegram.InlineKeyboardMarkup(keyboard)
        update.message.reply_text('Больше ничего не найдено, поиск завершен. /find чтобы начать новый поиск, /repeat чтобы повторить последний поиск.',
                                  reply_markup=reply_markup, parse_mode=telegram.ParseMode.MARKDOWN)
        return ConversationHandler.END
    elif link_dict[update.message.chat_id][0][0] == -1:
        keyboard = [[telegram.InlineKeyboardButton("Find", callback_data='find')],
                    [telegram.InlineKeyboardButton("Repeat", callback_data='repeat')]]
        reply_markup = telegram.InlineKeyboardMarkup(keyboard)
        update.message.reply_text(
            'Не получилось обойти капчу, попробуйте повторить запрос еще раз позже.',
            reply_markup=reply_markup, parse_mode=telegram.ParseMode.MARKDOWN)
        return ConversationHandler.END
    else:
        link = epn_parse.get_cashback_link(cookie_list, link_dict[update.message.chat_id][0][0])
        if link:
            bot.send_message(parse_mode=telegram.ParseMode.MARKDOWN, chat_id=update.message.chat_id,
                             text="Неправильный бренд, бренд товара " + link_dict[update.message.chat_id][0][1] +
                                  " не совпадает с брендами " + str(user_data['brand']) + "\n[!](" +
                                  link_dict[update.message.chat_id][
                                      0][0] + ")[Нажми на ссылку чтобы заказать!](" + link + ")")
        else:
            bot.send_message(parse_mode=telegram.ParseMode.MARKDOWN, chat_id=update.message.chat_id,
                             text="Неправильный бренд, бренд товара " + link_dict[update.message.chat_id][0][1] +
                                  " не совпадает с брендами " + str(user_data['brand']) +
                                  "\n[Нажми на ссылку чтобы заказать!](" + link_dict[update.message.chat_id][0][
                                      0] + ")")
        keyboard = [[telegram.InlineKeyboardButton("Да", callback_data='да'),
                     telegram.InlineKeyboardButton("Нет", callback_data='нет')]]
        reply_markup = telegram.InlineKeyboardMarkup(keyboard)
        update.message.reply_text('Искать дальше? Да/Нет (д/н либо /yes или /no)', reply_markup=reply_markup)
        return SEARCH_NEXT


@run_async
def begin(bot, update, user_data):
    if update.callback_query:
        query = update.callback_query
        update = query
    else:
        query = ''
    if query and query.data == 'repeat':
        if ('product' not in user_data) or ('brand' not in user_data):
            keyboard = [[telegram.InlineKeyboardButton("Find", callback_data='find')]]
            reply_markup = telegram.InlineKeyboardMarkup(keyboard)
            update.message.reply_text('В предыдущем поиске не задан бренд или поиск. /find чтобы начать новый поиск.',
                                      reply_markup=reply_markup, parse_mode=telegram.ParseMode.MARKDOWN)
            return ConversationHandler.END
        update.message.reply_text('Повторяем предыдущий поиск!')
        link_dict[update.message.chat_id] = []
        condition_result_ready_dict[update.message.chat_id] = threading.Condition()
        condition_user_ready_dict[update.message.chat_id] = threading.Condition()
        threading.Thread(name='refund_thread',
                         target=AliExpress.find_refund,
                         args=(
                             user_data, link_dict[update.message.chat_id],
                             condition_result_ready_dict[update.message.chat_id],
                             condition_user_ready_dict[update.message.chat_id])).start()
        with condition_result_ready_dict[update.message.chat_id]:
            if not condition_result_ready_dict[update.message.chat_id].wait(TIMEOUT):
                keyboard = [[telegram.InlineKeyboardButton("Find", callback_data='find')],
                            [telegram.InlineKeyboardButton("Repeat", callback_data='repeat')]]
                reply_markup = telegram.InlineKeyboardMarkup(keyboard)
                update.message.reply_text('Поиск завершен по таймауту. /find чтобы начать новый поиск.',
                                          reply_markup=reply_markup, parse_mode=telegram.ParseMode.MARKDOWN)
                return ConversationHandler.END
        if link_dict[update.message.chat_id][0] is None:
            keyboard = [[telegram.InlineKeyboardButton("Find", callback_data='find')],
                        [telegram.InlineKeyboardButton("Repeat", callback_data='repeat')]]
            reply_markup = telegram.InlineKeyboardMarkup(keyboard)
            update.message.reply_text(
                'Больше ничего не найдено, поиск завершен. /find чтобы начать новый поиск, /repeat чтобы повторить последний поиск.',
                reply_markup=reply_markup, parse_mode=telegram.ParseMode.MARKDOWN)
            return ConversationHandler.END
        elif link_dict[update.message.chat_id][0][0] == -1:
            keyboard = [[telegram.InlineKeyboardButton("Find", callback_data='find')],
                        [telegram.InlineKeyboardButton("Repeat", callback_data='repeat')]]
            reply_markup = telegram.InlineKeyboardMarkup(keyboard)
            update.message.reply_text(
                'Не получилось обойти капчу, попробуйте повторить запрос еще раз позже.',
                reply_markup=reply_markup, parse_mode=telegram.ParseMode.MARKDOWN)
            return ConversationHandler.END
        else:
            link = epn_parse.get_cashback_link(cookie_list, link_dict[update.message.chat_id][0][0])
            if link:
                bot.send_message(parse_mode=telegram.ParseMode.MARKDOWN, chat_id=update.message.chat_id,
                                 text="Неправильный бренд, бренд товара " + link_dict[update.message.chat_id][0][1] +
                                      " не совпадает с брендами " + str(user_data['brand']) + "\n[!](" +
                                      link_dict[update.message.chat_id][
                                          0][0] + ")[Нажми на ссылку чтобы заказать!](" + link + ")")
            else:
                bot.send_message(parse_mode=telegram.ParseMode.MARKDOWN, chat_id=update.message.chat_id,
                                 text="Неправильный бренд, бренд товара " + link_dict[update.message.chat_id][0][1] +
                                      " не совпадает с брендами " + str(user_data['brand']) +
                                      "\n[Нажми на ссылку чтобы заказать!](" + link_dict[update.message.chat_id][0][
                                          0] + ")")
            keyboard = [[telegram.InlineKeyboardButton("Да", callback_data='да'),
                         telegram.InlineKeyboardButton("Нет", callback_data='нет')]]
            reply_markup = telegram.InlineKeyboardMarkup(keyboard)
            update.message.reply_text('Искать дальше? Да/Нет (д/н либо /yes или /no)', reply_markup=reply_markup)
            return SEARCH_NEXT
    else:
        update_db(update)
        keyboard = [[telegram.InlineKeyboardButton("Cancel", callback_data='cancel')],
                       [telegram.InlineKeyboardButton("Repeat last", callback_data='repeat_last')]]
        reply_markup = telegram.InlineKeyboardMarkup(keyboard)
        bot.send_message(parse_mode=telegram.ParseMode.MARKDOWN, reply_markup=reply_markup, chat_id=update.message.chat_id, text= WELCOME_TEXT)
        return PRODUCT_CHOOSE


def product_reply(bot, update, user_data):
    if update.callback_query:
        if update.callback_query.data == 'cancel':
            return cancel(bot, update, user_data)
        elif update.callback_query.data == 'repeat_last':
            query = update.callback_query
            update = query
            if 'product' not in user_data:
                update.message.reply_text(
                    'Продукт в прошлом поиске не был задан!')
                return cancel(bot, update, user_data)
            keyboard = [[telegram.InlineKeyboardButton("Skip", callback_data='skip')],
                        [telegram.InlineKeyboardButton("Repeat last", callback_data='repeat_last')],
                        [telegram.InlineKeyboardButton("Cancel", callback_data='cancel')]]
            reply_markup = telegram.InlineKeyboardMarkup(keyboard)
            update.message.reply_text(
                'Поиск ' + user_data['product'] + '! Введите диапазон цен в формате 10-30 (в долларах) (/skip чтобы пропустить ввод цен):',
                reply_markup=reply_markup, parse_mode=telegram.ParseMode.MARKDOWN)
            return PRICE_RANGE_CHOOSE
    text = update.message.text
    user_data['product'] = text
    keyboard = [[telegram.InlineKeyboardButton("Skip", callback_data='skip')],
                [telegram.InlineKeyboardButton("Repeat last", callback_data='repeat_last')],
                [telegram.InlineKeyboardButton("Cancel", callback_data='cancel')]]
    reply_markup = telegram.InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Поиск сохранен! Введите диапазон цен в формате 10-30 (в долларах) (/skip чтобы пропустить ввод цен):',
                              reply_markup=reply_markup, parse_mode=telegram.ParseMode.MARKDOWN)
    return PRICE_RANGE_CHOOSE


def price_range_reply(bot, update, user_data):
    if update.callback_query:
        if update.callback_query.data == 'cancel':
            return cancel(bot, update, user_data)
        elif update.callback_query.data == 'repeat_last':
            query = update.callback_query
            update = query
            if 'min_price' not in user_data or 'max_price' not in user_data:
                update.message.reply_text(
                    'Максимальная или минимальная цена не были заданы в прошлом поиске!')
                return cancel(bot, update, user_data)
            keyboard = [[telegram.InlineKeyboardButton("Skip", callback_data='skip')],
                        [telegram.InlineKeyboardButton("Repeat last", callback_data='repeat_last')],
                        [telegram.InlineKeyboardButton("Cancel", callback_data='cancel')]]
            reply_markup = telegram.InlineKeyboardMarkup(keyboard)
            update.message.reply_text(
                'Диапазон цен ' + user_data['min_price'] + '-' + user_data['max_price'] + '! Введите слова для фильтрации, которые надо исключить из поиска, через запятую (например case,for,glass) (/skip чтобы пропустить ввод фильтров):',
                reply_markup=reply_markup, parse_mode=telegram.ParseMode.MARKDOWN)
            return FILTER_WORDS_CHOOSE
    text = update.message.text
    prices = text.split('-')
    if len(prices) < 2:
        update.message.reply_text(
            'Вы ввели диапазон цен неправильно, диапазон не сохранен. '
            'Введите слова для фильтрации, которые надо исключить из поиска, через запятую (например case,for,glass) (/skip чтобы пропустить ввод фильтров):')
        user_data['min_price'] = ''
        user_data['max_price'] = ''
        return FILTER_WORDS_CHOOSE
    min_price = prices[0]
    if not min_price:
        min_price = ''
    max_price = prices[1]
    if not max_price:
        max_price = ''
    user_data['min_price'] = min_price
    user_data['max_price'] = max_price
    keyboard = [[telegram.InlineKeyboardButton("Skip", callback_data='skip')],
                [telegram.InlineKeyboardButton("Repeat last", callback_data='repeat_last')],
                [telegram.InlineKeyboardButton("Cancel", callback_data='cancel')]]
    reply_markup = telegram.InlineKeyboardMarkup(keyboard)
    update.message.reply_text(
        'Диапазон цен сохранен! Введите слова для фильтрации, которые надо исключить из поиска, через запятую (например case,for,glass) (/skip чтобы пропустить ввод фильтров):',
        reply_markup=reply_markup, parse_mode=telegram.ParseMode.MARKDOWN)
    return FILTER_WORDS_CHOOSE


def skip_price_range_reply(bot, update, user_data):
    if update.callback_query:
        query = update.callback_query
        update = query
        if query.data == 'cancel':
            return cancel(bot, update, user_data)
        elif query.data == 'repeat_last':
            if 'min_price' not in user_data or 'max_price' not in user_data:
                update.message.reply_text(
                    'Максимальная или минимальная цена не были заданы в прошлом поиске!')
                return cancel(bot, update, user_data)
            keyboard = [[telegram.InlineKeyboardButton("Skip", callback_data='skip')],
                        [telegram.InlineKeyboardButton("Repeat last", callback_data='repeat_last')],
                        [telegram.InlineKeyboardButton("Cancel", callback_data='cancel')]]
            reply_markup = telegram.InlineKeyboardMarkup(keyboard)
            update.message.reply_text(
                'Диапазон цен ' + user_data['min_price'] + '-' + user_data[
                    'max_price'] + '! Введите слова для фильтрации, которые надо исключить из поиска, через запятую (например case,for,glass) (/skip чтобы пропустить ввод фильтров):',
                reply_markup=reply_markup, parse_mode=telegram.ParseMode.MARKDOWN)
            return FILTER_WORDS_CHOOSE
    user_data['min_price'] = ''
    user_data['max_price'] = ''
    keyboard = [[telegram.InlineKeyboardButton("Skip", callback_data='skip')],
                [telegram.InlineKeyboardButton("Repeat last", callback_data='repeat_last')],
                [telegram.InlineKeyboardButton("Cancel", callback_data='cancel')]]
    reply_markup = telegram.InlineKeyboardMarkup(keyboard)
    update.message.reply_text(
        'Диапазон не задан. Введите слова для фильтрации через запятую (например case,for,glass) (/skip чтобы пропустить ввод фильтров):',
        reply_markup=reply_markup, parse_mode=telegram.ParseMode.MARKDOWN)
    return FILTER_WORDS_CHOOSE


def filter_reply(bot, update, user_data):
    if update.callback_query:
        if update.callback_query.data == 'cancel':
            return cancel(bot, update, user_data)
        elif update.callback_query.data == 'repeat_last':
            query = update.callback_query
            update = query
            if 'filter_words' not in user_data:
                update.message.reply_text(
                    'Фильтры не были заданы в прошлом поиске!')
                return cancel(bot, update, user_data)
            keyboard = [[telegram.InlineKeyboardButton("Repeat last", callback_data='repeat_last')],
                        [telegram.InlineKeyboardButton("Cancel", callback_data='cancel')]]
            reply_markup = telegram.InlineKeyboardMarkup(keyboard)
            update.message.reply_text('Фильтры ' + str(user_data['filter_words']) + '! Введите бренд (можно несколько, через запятую) '
                                      '(например "Xiaomi,Amazfit"):',
                                      reply_markup=reply_markup, parse_mode=telegram.ParseMode.MARKDOWN)
            return BRAND_CHOOSE
    text = update.message.text
    filter_words = text.split(',')
    if not filter_words:
        filter_words = []
    user_data['filter_words'] = filter_words
    keyboard = [[telegram.InlineKeyboardButton("Repeat last", callback_data='repeat_last')],
                [telegram.InlineKeyboardButton("Cancel", callback_data='cancel')]]
    reply_markup = telegram.InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Фильтры сохранены! Введите бренд (можно несколько, через запятую) '
                              '(например "Xiaomi,Amazfit"):',
                              reply_markup=reply_markup, parse_mode=telegram.ParseMode.MARKDOWN)
    return BRAND_CHOOSE


def skip_filter_reply(bot, update, user_data):
    if update.callback_query:
        query = update.callback_query
        update = query
        if query.data == 'cancel':
            return cancel(bot, update, user_data)
        elif query.data == 'repeat_last':
            if 'filter_words' not in user_data:
                update.message.reply_text(
                    'Фильтры не были заданы в прошлом поиске!')
                return cancel(bot, update, user_data)
            keyboard = [[telegram.InlineKeyboardButton("Repeat last", callback_data='repeat_last')],
                        [telegram.InlineKeyboardButton("Cancel", callback_data='cancel')]]
            reply_markup = telegram.InlineKeyboardMarkup(keyboard)
            update.message.reply_text(
                'Фильтры ' + str(user_data['filter_words']) + '! Введите бренд (можно несколько, через запятую) '
                                                              '(например "Xiaomi,Amazfit"):',
                reply_markup=reply_markup, parse_mode=telegram.ParseMode.MARKDOWN)
            return BRAND_CHOOSE
    user_data['filter_words'] = []
    keyboard = [[telegram.InlineKeyboardButton("Cancel", callback_data='cancel')]]
    reply_markup = telegram.InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Фильтры не заданы. Введите бренд (можно несколько, через запятую) '
                              '(например "Xiaomi,Amazfit"):', reply_markup=reply_markup)
    return BRAND_CHOOSE


@run_async
def brand_reply(bot, update, user_data):
    if update.callback_query:
        if update.callback_query.data == 'cancel':
            return cancel(bot, update, user_data)
        elif update.callback_query.data == 'repeat_last':
            query = update.callback_query
            update = query
            if 'brand' not in user_data:
                update.message.reply_text(
                    'Бренды в прошлом поиске не были заданы!')
                return cancel(bot, update, user_data)
            update.message.reply_text('Бренды ' + str(user_data['brand']) + '! Начинаем поиск!')
    else:
        text = update.message.text
        brand_words = text.lower().split(',')
        if not brand_words:
            brand_words = []
        user_data['brand'] = brand_words
        update.message.reply_text('Бренд сохранен! Начинаем поиск!')
    link_dict[update.message.chat_id] = []
    condition_result_ready_dict[update.message.chat_id] = threading.Condition()
    condition_user_ready_dict[update.message.chat_id] = threading.Condition()
    threading.Thread(name='refund_thread',
                     target=AliExpress.find_refund,
                     args=(user_data, link_dict[update.message.chat_id], condition_result_ready_dict[update.message.chat_id], condition_user_ready_dict[update.message.chat_id])).start()
    with condition_result_ready_dict[update.message.chat_id]:
        if not condition_result_ready_dict[update.message.chat_id].wait(TIMEOUT):
            keyboard = [[telegram.InlineKeyboardButton("Find", callback_data='find')],
                        [telegram.InlineKeyboardButton("Repeat", callback_data='repeat')]]
            reply_markup = telegram.InlineKeyboardMarkup(keyboard)
            update.message.reply_text('Поиск завершен по таймауту. /find чтобы начать новый поиск, /repeat чтобы повторить последний поиск.',
                                      reply_markup=reply_markup, parse_mode=telegram.ParseMode.MARKDOWN)
            return ConversationHandler.END
    if link_dict[update.message.chat_id][0] is None:
        keyboard = [[telegram.InlineKeyboardButton("Find", callback_data='find')],
                    [telegram.InlineKeyboardButton("Repeat", callback_data='repeat')]]
        reply_markup = telegram.InlineKeyboardMarkup(keyboard)
        update.message.reply_text('Больше ничего не найдено, поиск завершен. /find чтобы начать новый поиск, /repeat чтобы повторить последний поиск.',
                                  reply_markup=reply_markup, parse_mode=telegram.ParseMode.MARKDOWN)
        return ConversationHandler.END
    elif link_dict[update.message.chat_id][0][0] == -1:
        bot.send_message(chat_id=MY_ID,
                     text='Seems like bot stopped to work, fix me!', parse_mode=telegram.ParseMode.MARKDOWN)
        keyboard = [[telegram.InlineKeyboardButton("Find", callback_data='find')],
                    [telegram.InlineKeyboardButton("Repeat", callback_data='repeat')]]
        reply_markup = telegram.InlineKeyboardMarkup(keyboard)
        update.message.reply_text('Кажется, Алиэкспресс заблокировал поиск каптчой, к сожалению проблема пока неразрешима, попробуйте повторить поиск позже.',
                                  reply_markup=reply_markup, parse_mode=telegram.ParseMode.MARKDOWN)
        return ConversationHandler.END
    else:
        link = epn_parse.get_cashback_link(cookie_list, link_dict[update.message.chat_id][0][0])
        if link:
            bot.send_message(parse_mode=telegram.ParseMode.MARKDOWN, chat_id=update.message.chat_id,
                             text="Неправильный бренд, бренд товара " + link_dict[update.message.chat_id][0][1] + 
                             " не совпадает с брендами " + str(user_data['brand']) + "\n[!](" +
                                  link_dict[update.message.chat_id][
                                      0][0] + ")[Нажми на ссылку чтобы заказать!](" + link + ")")
        else:
            bot.send_message(parse_mode=telegram.ParseMode.MARKDOWN, chat_id=update.message.chat_id,
                             text="Неправильный бренд, бренд товара " + link_dict[update.message.chat_id][0][1] + 
                             " не совпадает с брендами " + str(user_data['brand']) + 
                             "\n[Нажми на ссылку чтобы заказать!](" + link_dict[update.message.chat_id][0][0] + ")")
        keyboard = [[telegram.InlineKeyboardButton("Да", callback_data='да'),
                     telegram.InlineKeyboardButton("Нет", callback_data='нет')]]
        reply_markup = telegram.InlineKeyboardMarkup(keyboard)
        update.message.reply_text('Искать дальше? Да/Нет (д/н либо /yes или /no)', reply_markup=reply_markup)
        return SEARCH_NEXT


@run_async
def answer_yes(bot, update, user_data):
    with condition_user_ready_dict[update.message.chat_id]:
        condition_user_ready_dict[update.message.chat_id].notifyAll()
    with condition_result_ready_dict[update.message.chat_id]:
        if not condition_result_ready_dict[update.message.chat_id].wait(TIMEOUT):
            keyboard = [[telegram.InlineKeyboardButton("Find", callback_data='find')],
                        [telegram.InlineKeyboardButton("Repeat", callback_data='repeat')]]
            reply_markup = telegram.InlineKeyboardMarkup(keyboard)
            update.message.reply_text('Поиск завершен по таймауту. /find чтобы начать новый поиск, /repeat чтобы повторить последний поиск.',
                                      reply_markup=reply_markup, parse_mode=telegram.ParseMode.MARKDOWN)
            return ConversationHandler.END
    if link_dict[update.message.chat_id][0] is None:
        keyboard = [[telegram.InlineKeyboardButton("Find", callback_data='find')],
                    [telegram.InlineKeyboardButton("Repeat", callback_data='repeat')]]
        reply_markup = telegram.InlineKeyboardMarkup(keyboard)
        update.message.reply_text('Больше ничего не найдено, поиск завершен. /find чтобы начать новый поиск, /repeat чтобы повторить последний поиск.',
                                  reply_markup=reply_markup, parse_mode=telegram.ParseMode.MARKDOWN)
        return ConversationHandler.END
    elif link_dict[update.message.chat_id][0][0] == -1:
        bot.send_message(chat_id=MY_ID,
                     text='Seems like bot stopped to work, fix me!', parse_mode=telegram.ParseMode.MARKDOWN)
        keyboard = [[telegram.InlineKeyboardButton("Find", callback_data='find')],
                    [telegram.InlineKeyboardButton("Repeat", callback_data='repeat')]]
        reply_markup = telegram.InlineKeyboardMarkup(keyboard)
        update.message.reply_text('Кажется, Алиэкспресс заблокировал поиск каптчой, к сожалению проблема пока неразрешима, попробуйте повторить поиск позже.',
                                  reply_markup=reply_markup, parse_mode=telegram.ParseMode.MARKDOWN)
        return ConversationHandler.END
    else:
        link = epn_parse.get_cashback_link(cookie_list, link_dict[update.message.chat_id][0][0])
        if link:
            bot.send_message(parse_mode=telegram.ParseMode.MARKDOWN, chat_id=update.message.chat_id,
                             text="Неправильный бренд, бренд товара " + link_dict[update.message.chat_id][0][1] + 
                             " не совпадает с брендами " + str(user_data['brand']) + "\n[!](" +
                                  link_dict[update.message.chat_id][
                                      0][0] + ")[Нажми на ссылку чтобы заказать!](" + link + ")")
        else:
            bot.send_message(parse_mode=telegram.ParseMode.MARKDOWN, chat_id=update.message.chat_id,
                             text="Неправильный бренд, бренд товара " + link_dict[update.message.chat_id][0][1] + 
                             " не совпадает с брендами " + str(user_data['brand']) + 
                             "\n[Нажми на ссылку чтобы заказать!](" + link_dict[update.message.chat_id][0][0] + ")")
        keyboard = [[telegram.InlineKeyboardButton("Да", callback_data='да'),
                         telegram.InlineKeyboardButton("Нет", callback_data='нет')]]
        reply_markup = telegram.InlineKeyboardMarkup(keyboard)
        update.message.reply_text('Искать дальше? Да/Нет (д/н либо /yes или /no)', reply_markup=reply_markup)
        return SEARCH_NEXT


@run_async
def answer_no(bot, update, user_data):
    keyboard = [[telegram.InlineKeyboardButton("Find", callback_data='find')],
                [telegram.InlineKeyboardButton("Repeat", callback_data='repeat')]]
    reply_markup = telegram.InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Хорошо, поиск завершен. /find чтобы начать новый поиск, /repeat чтобы повторить последний поиск.',
                              reply_markup=reply_markup, parse_mode=telegram.ParseMode.MARKDOWN)
    return ConversationHandler.END

@run_async
def search_next(bot, update, user_data):
    if update.message:
        text = update.message.text
    else:
        text = ''
    if update.callback_query:
        query = update.callback_query
        update = query
    else:
        query = ''
    if text.lower() == 'да' or text.lower() == 'д' or (query and query.data == 'да'):
        with condition_user_ready_dict[update.message.chat_id]:
            condition_user_ready_dict[update.message.chat_id].notifyAll()
        with condition_result_ready_dict[update.message.chat_id]:
            if not condition_result_ready_dict[update.message.chat_id].wait(TIMEOUT):
                keyboard = [[telegram.InlineKeyboardButton("Find", callback_data='find')],
                            [telegram.InlineKeyboardButton("Repeat", callback_data='repeat')]]
                reply_markup = telegram.InlineKeyboardMarkup(keyboard)
                update.message.reply_text('Поиск завершен по таймауту. /find чтобы начать новый поиск, /repeat чтобы повторить последний поиск.',
                                          reply_markup=reply_markup, parse_mode=telegram.ParseMode.MARKDOWN)
                return ConversationHandler.END
        if link_dict[update.message.chat_id][0] is None:
            keyboard = [[telegram.InlineKeyboardButton("Find", callback_data='find')],
                        [telegram.InlineKeyboardButton("Repeat", callback_data='repeat')]]
            reply_markup = telegram.InlineKeyboardMarkup(keyboard)
            update.message.reply_text('Больше ничего не найдено, поиск завершен. /find чтобы начать новый поиск, /repeat чтобы повторить последний поиск.',
                                      reply_markup=reply_markup, parse_mode=telegram.ParseMode.MARKDOWN)
            return ConversationHandler.END
        else:
            link = epn_parse.get_cashback_link(cookie_list, link_dict[update.message.chat_id][0][0])
            if link:
                bot.send_message(parse_mode=telegram.ParseMode.MARKDOWN, chat_id=update.message.chat_id,
                                text="Неправильный бренд, бренд товара " + link_dict[update.message.chat_id][0][1] + 
                                " не совпадает с брендами " + str(user_data['brand']) + "\n[!](" +
                                    link_dict[update.message.chat_id][
                                        0][0] + ")[Нажми на ссылку чтобы заказать!](" + link + ")")
            else:
                bot.send_message(parse_mode=telegram.ParseMode.MARKDOWN, chat_id=update.message.chat_id,
                                text="Неправильный бренд, бренд товара " + link_dict[update.message.chat_id][0][1] + 
                                " не совпадает с брендами " + str(user_data['brand']) + 
                                "\n[Нажми на ссылку чтобы заказать!](" + link_dict[update.message.chat_id][0][0] + ")")
            keyboard = [[telegram.InlineKeyboardButton("Да", callback_data='да'),
                         telegram.InlineKeyboardButton("Нет", callback_data='нет')]]
            reply_markup = telegram.InlineKeyboardMarkup(keyboard)
            update.message.reply_text('Искать дальше? Да/Нет (д/н либо /yes или /no)', reply_markup=reply_markup)
            return SEARCH_NEXT
    else:
        keyboard = [[telegram.InlineKeyboardButton("Find", callback_data='find')],
                    [telegram.InlineKeyboardButton("Repeat", callback_data='repeat')]]
        reply_markup = telegram.InlineKeyboardMarkup(keyboard)
        update.message.reply_text('Хорошо, поиск завершен. /find чтобы начать новый поиск, /repeat чтобы повторить последний поиск.',
                                  reply_markup=reply_markup, parse_mode=telegram.ParseMode.MARKDOWN)
        return ConversationHandler.END


def cancel(bot, update, user_data):
    if hasattr(update, 'callback_query'):
        if update.callback_query:
            query = update.callback_query
            update = query
    keyboard = [[telegram.InlineKeyboardButton("Find", callback_data='find')]]
    reply_markup = telegram.InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Пока! Продолжим в следующий раз! /find чтобы начать новый поиск, /repeat чтобы повторить последний поиск.',
                              reply_markup=reply_markup, parse_mode=telegram.ParseMode.MARKDOWN)
    return ConversationHandler.END


def conversation_timeout(bot, update, user_data):
    keyboard = [[telegram.InlineKeyboardButton("Find", callback_data='find')],
                [telegram.InlineKeyboardButton("Repeat", callback_data='repeat')]]
    reply_markup = telegram.InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Ты думаешь слишком долго! Продолжим в следующий раз! /find чтобы начать новый поиск, /repeat чтобы повторить последний поиск.',
                              reply_markup=reply_markup, parse_mode=telegram.ParseMode.MARKDOWN)
    return ConversationHandler.END


def post_message(bot, update):
    users = get_all_users_from_db()
    for user in users:
        try:
            bot.forward_message(int(user[0]), update.message.chat_id, update.message.message_id)
        except:
            delete_user_from_db(user[0])
        #bot.send_message(chat_id=int(user[0]), text=update.message.text, parse_mode=ParseMode.MARKDOWN)
    update.message.reply_text('Готово! Пост опубликован!')
    return ConversationHandler.END


def print_message(bot, update):
    bot.send_message(chat_id=update.message.chat_id,
                     text=update.message.text, parse_mode=telegram.ParseMode.MARKDOWN)
    return ConversationHandler.END


def count_users(bot, update):
    users = get_all_users_from_db()
    bot.send_message(chat_id=update.message.chat_id,
                     text=('Количество юзеров в базе: ' + str(len(users))))


def begin_post(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text='Форвардни мне сообщение которое нужно опубликовать. /cancel для отмены.')
    return GET_MESSAGE_TO_POST


def begin_print(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text='Напиши мне сообщение которое нужно написать от моего имени. /cancel для отмены.')
    return GET_MESSAGE_TO_PRINT


def filters(bot, update):
    if update.callback_query:
        query = update.callback_query
        update = query
    keyboard = [[telegram.InlineKeyboardButton("Телефоны", callback_data='телефоны')],
                [telegram.InlineKeyboardButton("Вейпы", callback_data='вейпы')],
                [telegram.InlineKeyboardButton("Ноутбуки", callback_data='ноутбуки')],
                [telegram.InlineKeyboardButton("Cancel", callback_data='cancel')]]
    reply_markup = telegram.InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Выберите категорию, для которой вы хотите посмотреть фильтры.',
                              reply_markup=reply_markup, parse_mode=telegram.ParseMode.MARKDOWN)
    return CHOOSE_FILTERS


def choose_filters(bot, update, user_data):
    if update.callback_query:
        query = update.callback_query
        if query.data == 'cancel':
            return cancel(bot, update, user_data)
        elif query.data == 'вейпы':
            query.message.reply_text('Фильтры для вейпов:',
                                     parse_mode=telegram.ParseMode.MARKDOWN)
            query.message.reply_text('*' + vape_filters + '*',
                                      parse_mode=telegram.ParseMode.MARKDOWN)
            query.message.reply_text('*Замените <бренд> на название бренда вейпа.*',
                                     parse_mode=telegram.ParseMode.MARKDOWN)
            return ConversationHandler.END
        elif query.data == 'телефоны':
            query.message.reply_text('Фильтры для телефонов:',
                                     parse_mode=telegram.ParseMode.MARKDOWN)
            query.message.reply_text('*' + phone_filters + '*',
                                     parse_mode=telegram.ParseMode.MARKDOWN)
            query.message.reply_text('*Замените <бренд> на название бренда телефона.*',
                                     parse_mode=telegram.ParseMode.MARKDOWN)
            return ConversationHandler.END
        elif query.data == 'ноутбуки':
            query.message.reply_text('Фильтры для ноутбуков:',
                                     parse_mode=telegram.ParseMode.MARKDOWN)
            query.message.reply_text('*' + laptop_filters + '*',
                                     parse_mode=telegram.ParseMode.MARKDOWN)
            return ConversationHandler.END
        return ConversationHandler.END
    else:
        update.message.reply_text('Вы не нажали кнопку.',
                                  parse_mode=telegram.ParseMode.MARKDOWN)
        return ConversationHandler.END



def main():
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        level=logging.INFO)
    global updater
    global cookie_list
    dispatcher = updater.dispatcher
    start_handler = CommandHandler('start', start)
    help_handler = CommandHandler('help', help)
    iddqd_handler = CommandHandler('iddqd', iddqd)
    idfa_handler = CommandHandler('idfa', idfa)
    count_users_handler = CommandHandler('count', count_users)
    filters_handler = ConversationHandler(
        entry_points=[CommandHandler('filters', filters)],
        states={
            CHOOSE_FILTERS: [CallbackQueryHandler(choose_filters,
                                                  pass_user_data=True)
                                          ],
            ConversationHandler.TIMEOUT: [MessageHandler(Filters.text,
                                                         conversation_timeout,
                                                         pass_user_data=True),
                                          ]
        },
        fallbacks=[CommandHandler('cancel', cancel, pass_user_data=True)],
        conversation_timeout=TIMEOUT + 5
    )
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('find', begin, pass_user_data=True), CallbackQueryHandler(begin, pass_user_data=True),
                      CommandHandler('repeat', repeat, pass_user_data=True),
                      CommandHandler('test', test_search, pass_user_data=True)],
        states={
            PRODUCT_CHOOSE: [MessageHandler(Filters.text,
                                           product_reply,
                                           pass_user_data=True),
                             CommandHandler('yes',
                                            answer_yes,
                                            pass_user_data=True),
                             CommandHandler('no',
                                            answer_no,
                                            pass_user_data=True),
                             CallbackQueryHandler(product_reply,
                                                  pass_user_data=True)
                            ],
            BRAND_CHOOSE: [MessageHandler(Filters.text,
                                           brand_reply,
                                           pass_user_data=True),
                           CallbackQueryHandler(brand_reply,
                                                pass_user_data=True)
                            ],
            PRICE_RANGE_CHOOSE: [MessageHandler(Filters.text,
                                          price_range_reply,
                                          pass_user_data=True),
                                 CommandHandler('skip',
                                                skip_price_range_reply,
                                                pass_user_data=True),
                                 CallbackQueryHandler(skip_price_range_reply,
                                                      pass_user_data=True)
                           ],
            FILTER_WORDS_CHOOSE: [MessageHandler(Filters.text,
                                          filter_reply,
                                          pass_user_data=True),
                                 CommandHandler('skip',
                                                skip_filter_reply,
                                                pass_user_data=True),
                                CallbackQueryHandler(skip_filter_reply,
                                                       pass_user_data=True)
                           ],
            SEARCH_NEXT: [MessageHandler(Filters.text,
                                         search_next,
                                         pass_user_data=True),
                          CommandHandler('yes',
                                         answer_yes,
                                         pass_user_data=True),
                          CommandHandler('no',
                                         answer_no,
                                         pass_user_data=True),
                          CallbackQueryHandler(search_next,
                                               pass_user_data=True)
                            ],
            ConversationHandler.TIMEOUT: [MessageHandler(Filters.text,
                                                         conversation_timeout,
                                         pass_user_data=True),
                                          ]
        },
        fallbacks = [CommandHandler('cancel', cancel, pass_user_data=True)],
        conversation_timeout = TIMEOUT+5
    )
    conv_post_handler = ConversationHandler(
        entry_points=[CommandHandler('post', begin_post)],
        states={
            GET_MESSAGE_TO_POST: [MessageHandler(Filters.text,
                                                 post_message),
                                  ],
        },
        fallbacks=[CommandHandler('cancel', cancel, pass_user_data=True)],
        conversation_timeout=TIMEOUT+5
    )
    conv_print_handler = ConversationHandler(
        entry_points=[CommandHandler('print', begin_print)],
        states={
            GET_MESSAGE_TO_PRINT: [MessageHandler(Filters.text,
                                                 print_message),
                                  ],
        },
        fallbacks=[CommandHandler('cancel', cancel, pass_user_data=True)],
        conversation_timeout=TIMEOUT+5
    )
    text_handler = MessageHandler(Filters.text, text_reply, pass_user_data=True)
    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(help_handler)
    dispatcher.add_handler(iddqd_handler)
    dispatcher.add_handler(idfa_handler)
    dispatcher.add_handler(filters_handler)
    dispatcher.add_handler(conv_handler)
    dispatcher.add_handler(conv_post_handler)
    dispatcher.add_handler(count_users_handler)
    dispatcher.add_handler(conv_print_handler)
    dispatcher.add_handler(text_handler)
    #epn_parse.login_epn()
    updater.start_polling(poll_interval = 1.0, timeout=20)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        exit()
