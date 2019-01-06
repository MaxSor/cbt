#!/usr/bin/env python
# -*- coding: utf-8 -*-

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from pyvirtualdisplay import Display
from selenium import webdriver
import time
import queue
import threading
import os

#from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import logging

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

def initcredentials ():
    """ Read urls, telegram bot token and chat_id from file """
    logger.info('Initializing credentials')
    urllist = []
    bottoken = ''
    chat_id = ''

    filename = 'credentials'

    try:
        credentials_file = open(filename,'r')
    except:
        logger.critical('Error while read credentials file', exc_info = 1)
        exit()
    else:
        bottoken = credentials_file.readline().strip()
        chat_id = int(credentials_file.readline().strip())
        urllist.append(credentials_file.readline().strip())
        urllist.append(credentials_file.readline().strip())
        urllist.append(credentials_file.readline().strip())
        credentials_file.close
        logger.info("Initializing credentials finished")
    return urllist, bottoken, chat_id

urllist, bottoken, chat_id = initcredentials()

def initbrowser():
        """ Enable scrapping """
        display = Display(visible=0, size=(800, 600))
        display.start()
        browser = webdriver.Firefox(firefox_profile=webdriver.FirefoxProfile(), log_path=os.devnull)
        return browser, display

def disablebrowser(browser, display):
        """ Disable scrapper """
        browser.quit()
        display.stop()
    
def checkticketurl(url, browser, display):
        """Chek single url for available tickets"""
        tickets = 0
        msg = ''
        
        logger.info("Checking %s", url)
        try:
               browser.get(url)
        except:
               logger.error("Error while getting the url %s.", url, exc_info = 1)
               return tickets, msg

        try:
                text = browser.find_element_by_tag_name('h1').text
        except Exception as e:
                msg = str(e)[:-1] + " " + url
                logger.warn(msg)
                tickets = 1
        else:
                if (text != "Билетов нет") : 
                        msg = "Билеты есть? " + url
                        logger.warn(msg)
                        tickets = 1
                elif (text == "Билетов нет") : 
                        msg = ''
                        tickets = 0
        return tickets, msg

def checktickets(q):
    """Chek tickets by scrapping multiply urls"""
    
    waitsec = 10
    rowcount = 2
    urlresult = dict(zip(urllist,[0,0,0]))

    logger.info("Start checking urls)

    while True:
        browser, display = initbrowser()

        for url in urllist:
            tickets, msg = checkticketurl(url, browser, display)  
            #Notify when positive checks come in a row
            urlresult[url] += tickets
            if urlresult[url] == rowcount:
                urlresult[url] = 0
                logger.warn("Need to notify. %s in a row", rowcount)
                q.put(msg)    
        
        disablebrowser(browser, display)
        logger.info("Wait after next attempt %s sec", waitsec)
        time.sleep(waitsec)
        q.join()

def notify(bot, text):
    """Notify me"""
    bot.send_message(chat_id=chat_id, text=text)


def main():

    logger.info('Main started')
    
    def notifier(q):
        while(True):
            msg = q.get()
            logger.warn("---Notify: %s ---", msg)
            notify(bot, msg)
            q.task_done() 

    # Start the Bot
    updater = Updater(token=bottoken)
    bot = updater.bot
    updater.start_polling()

    # Start scrapling and notifiyng threads
    q = queue.Queue(maxsize = 0)   
    t = threading.Thread(name = "ProducerThread", target=checktickets, args=(q,))
    t.start()
    t = threading.Thread(name = "ConsumerThread", target=notifier, args=(q,))
    t.start()
    q.join
    
    logger.info('Threads started')

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()

if __name__ == '__main__':
    main()