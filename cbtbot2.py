#!/usr/bin/env python
# -*- coding: utf-8 -*-

from sys import argv
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from pyvirtualdisplay import Display
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By

import os
import time
import queue
import threading
import collections

#from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import logging

#Logging level is first param
# CRITICAL 	50
# ERROR 	40
# WARNING 	30
# INFO 	    20
# DEBUG 	10
# NOTSET 	0

print("Params", argv)

if len(argv)>1:
    print("First param is", argv[1])
    logging_level = int(argv[1]) 
else:
    logging_level = 20

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging_level)

logger = logging.getLogger(__name__)

waitsec = 60 #Wait before next attempt

def initcredentials ():
    """ Read urls, telegram bot token and chat_id from file """
    logger.debug('Initializing credentials')
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
        logger.debug("Initializing credentials finished")
    return urllist, bottoken, chat_id

urllist, bottoken, chat_id = initcredentials()
display = Display(visible=0, size=(800, 600))
display.start()


def initbrowser():
        """ Enable scrapping """
        
        browser_type = 'chrome'
        logger.debug("Initiating browser %s", browser_type)
        
        # display = Display(visible=0, size=(800, 600))
        # display.start()
        notbrowser_not_created = True
        while notbrowser_not_created:
            try:
                if browser_type == 'ff':
                    browser = webdriver.Firefox(firefox_profile=webdriver.FirefoxProfile(), log_path=os.devnull)
                    logger.debug("Firefox browser inited")
                else:
                    options = webdriver.ChromeOptions()
                    options.add_argument("--no-sandbox") # Bypass OS security model
                    browser = webdriver.Chrome(options = options, executable_path="/usr/bin/chromedriver")
                    logger.debug("Chrome browser inited")            
                notbrowser_not_created = False
                break
            except:
                logger.error("Error while browser init", exc_info = 1)
                continue      
        return browser

def disablebrowser(browser):
        """ Disable scrapper """
        browser.quit()
        logger.debug("Browser stopped")
    
def checkticketurl(url, browser):
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
                text = WebDriverWait(browser, 20).until(lambda x: x.find_element_by_tag_name('h2')).text
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
    
    rowcount = 1
    urlresult = dict(zip(urllist,[0,0,0]))
    
    logger.info("Ticket parser started")
    browser = initbrowser()

    while True:
        try:
            for url in urllist:
                tickets, msg = checkticketurl(url, browser)  
                #Notify when positive checks come in a row
                urlresult[url] += tickets
                if urlresult[url] == rowcount:
                    urlresult[url] = 0
                    logger.warn("Need to notify. %s in a row", rowcount)
                    q.put(msg)
        except:
            browser = initbrowser()
            continue 
        # disablebrowser(browser)
        q.join()
        logger.debug("Wait after next attempt %s sec", waitsec)
        time.sleep(waitsec)

def parseAvitoSearch (url, css_selector, browser):
    """Parse search results"""
    result = collections.defaultdict(list)
    logger.info("Checking %s", url)
    try:
        browser.get(url) #"https://www.avito.ru/moskva?s_trg=3&q=carbon+based+lifeforms"
        logger.debug("Got %s", url)
        items = browser.find_elements(By.CSS_SELECTOR, css_selector) #".item.item_table"
        for item in items:
            text = item.find_element(By.CSS_SELECTOR, "h3").text
            link = item.find_element(By.TAG_NAME, "a").get_attribute('href')
            price = item.find_element(By.CSS_SELECTOR, ".price").get_attribute('content')
            result[link].append([text,price])
    except:
        logger.error("Error while parsing avito search results", exc_info = 1)
        return
    return result

def parseAvito (q):
    """Monitor avito and send message to queue when search results changes"""

    logger.info("Avito parser started")
    AvitoAdLinklist = collections.defaultdict(list)
    
    logger.debug("Before avito browser init")
    browser = initbrowser()
    logger.debug("After avito browser init")    

    while True:
        try:
            AvitoAdLinklist2 = parseAvitoSearch ("https://www.avito.ru/moskva?s_trg=3&q=carbon+based+lifeforms", ".item.item_table", browser)
            logger.info("After avito url parsed")
            # AvitoAdLinklist = parseAvitoSearch ("https://www.avito.ru/moskva?s_trg=3&q=carbon+based+lifeforms", ".item", browser)  
        except:
            logger.error("Error while checking avito search results", exc_info = 1)
            browser = initbrowsNjer()
            continue

        # disablebrowser(browser)

        dif = set()
        if len(AvitoAdLinklist) == 0:
            # For first launch
            AvitoAdLinklist = AvitoAdLinklist2.copy()
        else: 
            dif = set(AvitoAdLinklist2).symmetric_difference(set(AvitoAdLinklist))

        if len(dif) > 0:
            msg = "Avito results changed " + str(dif)
            logger.warn(msg)
            q.put(msg)
        
        q.join()
        logger.debug("After avito result proceed")
        time.sleep(waitsec)

def notify(bot, text):
    """Notify me"""
    bot.send_message(chat_id=chat_id, text=text)


def main():

    logger.info("Main started")
    
    def notifier(q):
        while(True):
            msg = q.get()
            logger.warn("---Notify: %s ---", msg)
            notify(bot, msg)
            q.task_done() 

    # Start the Bot
    updater = Updater(token=bottoken)
    bot = updater.bot
    # updater.start_polling()

    # Start scrapling and notifiyng threads
    q = queue.Queue(maxsize = 0)   
    
    t = threading.Thread(name = "ProducerThread - Tickets", target=checktickets, args=(q,))
    t.start()
    
    # time.sleep(waitsec/2)

    # t = threading.Thread(name = "ProducerThread - Avito", target=parseAvito, args=(q,))
    # t.start()

    t = threading.Thread(name = "ConsumerThread - Telegram Notifier", target=notifier, args=(q,))
    t.start()

    q.join()
    
    logger.info("Threads started")

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()

if __name__ == '__main__':
    main()