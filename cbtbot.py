#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pyvirtualdisplay import Display
from selenium import webdriver
import time
import os

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import logging

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

# Enable scrapping
display = Display(visible=0, size=(800, 600))
display.start()
browser = webdriver.Firefox(firefox_profile=webdriver.FirefoxProfile(), log_path=os.devnull)

#Define variables

# Credentials file must have 5 lines
# 1st - AuthToken for Tg bot
# 2 - chat_id, 3-5 urls to check

path = 'credentials'
credentials_file = open(path,'r')

urls = []

bottoken = credentials_file.readline().strip()
chat_id = int(credentials_file.readline().strip())
urls.append(credentials_file.readline().strip())
urls.append(credentials_file.readline().strip())
urls.append(credentials_file.readline().strip())
credentials_file.close

# print(bottoken)
# print(chat_id)

def checktickets(urllist, bot, noticket):
    """Chek tickets by scrapping urls"""
    print("Start check")
    for url in urllist:
            print("Checking", url)
            browser.get(url)
            #time.sleep(3)
            try:
                    text = browser.find_element_by_tag_name('h2').text
            except Exception as e:
                    notify(bot, str(e) + " " + url)
                    #print("error")
                    noticket = 1
            else:
                    if (text != "Билетов нет") : 
                            notify(bot, "Билеты есть? " + url)
                            noticket = 1
                    elif (text == "Билетов нет") : 
                            #notify(bot, text)
                            noticket = 0
    print("Check complete, noticket = ", noticket)
    return noticket

def notify(bot, text):
    """Notify me"""
    bot.send_message(chat_id=chat_id, text=text)

def main():
    """Start the bot."""
    # Create the EventHandler and pass it your bot's token.
    updater = Updater(token=bottoken)
    bot = updater.bot
   
    # Start the Bot
    updater.start_polling()

    while True :
        noticket = 0
        noticket = checktickets(urls, bot, noticket)
        print(noticket)
        if noticket > 0 : 
                print("Sleep 600 sec")
                time.sleep(600)
        else :
                print("Sleep 60 sec")
                time.sleep(60)



    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()
    print("End")
   
    # Disable scrapper
    browser.quit()
    display.stop()

if __name__ == '__main__':
    main()


