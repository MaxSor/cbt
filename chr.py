#!/usr/bin/env python
# -*- coding: utf-8 -*-

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from pyvirtualdisplay import Display
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import time
import queue
import threading
import os

import collections

#from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import logging

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

def main():

        def initbrowser():
            """ Enable scrapping """
            
            browser_type = 'ff'
            
            display = Display(visible=0, size=(800, 600))
            display.start()

            if browser_type == 'ff':
                browser = webdriver.Firefox(firefox_profile=webdriver.FirefoxProfile(), log_path=os.devnull)
                logger.info("Firefox browser inited")
            else:
                options = webdriver.ChromeOptions()
                options.add_argument("--no-sandbox") # Bypass OS security model
                browser = webdriver.Chrome(options = options, executable_path="/usr/bin/chromedriver")
                logger.info("Chrome browser inited")
        
            return browser, display

        class AvitoAd:
            """Avito advert"""

            link_index = collections.defaultdict(list)

            def __init__(self, name, link, price):
                self.name = name
                self.link = link
                self.price = price
                AvitoAd.link_index[link].append(self)

            def __str__(self):
                return self.name + ' ' + self.price
            
            @classmethod
            def find_by_link(cls, link):
                return AvitoAd.link_index[link]

            @classmethod
            def count(cls):
                return len(AvitoAd.link_index)

        def parseAvitoSearch (url, css_selector):
            """Parse search results"""
            result = collections.defaultdict(list)
            try:
                browser.get(url) #"https://www.avito.ru/moskva?s_trg=3&q=carbon+based+lifeforms"
                items = browser.find_elements(By.CSS_SELECTOR, css_selector) #".item.item_table"
                logger.info("Browser got %s", url)
            except:
                logger.error("Error while parsing search results", exc_info = 1)
                return
            
            try:
                for item in items:
                    text = item.find_element(By.CSS_SELECTOR, "h3").text
                    link = item.find_element(By.TAG_NAME, "a").get_attribute('href')
                    price = item.find_element(By.CSS_SELECTOR, ".price").get_attribute('content')
                    result[link].append([text,price])
            except:
                logger.error("Error while collecting results", exc_info = 1)
                return 

            return result


        while True:
            browser, display = initbrowser()

            try:
                AvitoAdLinklist = parseAvitoSearch ("https://www.avito.ru/moskva?s_trg=3&q=carbon+based+lifeforms", ".item.item_table")
                AvitoAdLinklist2 = parseAvitoSearch ("https://www.avito.ru/moskva?s_trg=3&q=carbon+based+lifeforms", ".item")  
            except:
                logger.error("Error while checking urls", exc_info = 1)
                browser.quit()
                display.stop()
                continue

            dif = set()
            if len(AvitoAdLinklist) == 0:
                # For first launch
                AvitoAdLinklist = AvitoAdLinklist2.copy()
            else:
                dif = set(AvitoAdLinklist2).symmetric_difference(set(AvitoAdLinklist))

            if len(dif) > 0:
                print("dif: ", dif)
            
            browser.quit()
            display.stop()


            
        

        # text = browser.find_element_by_tag_name('h2').text
        # element = browser.find_element(By.CSS_SELECTOR, "h2")
        # print(element.text)
        # time.sleep(5) # Let the user actually see something!
        # search_box = browser.find_element_by_name('q')
        # search_box.send_keys('ChromeDriver')
        # search_box.submit()
        # time.sleep(5) # Let the user actually see something!

        browser.quit()
        display.stop()


if __name__ == '__main__':
    main()