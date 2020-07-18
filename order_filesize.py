#!/usr/bin/env python
# -*- coding: utf8
#
import pyocr.builders
import pyocr
import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait as WDW

import os
import time
from io import BytesIO
from PIL import Image
from PIL import ImageFilter
from PIL import ImageEnhance
import sys

import requests
import logging
download_dir = 'Z:\\'
logging.basicConfig(level=logging.ERROR,
                    format='(%(funcName)-10s) %(message)s')
cur_path = os.getcwd()

if os.path.exists("file_size.txt"):
    fo = open("file_size.txt", mode='a+')
else:
    fo = open("file_size.txt", "w")

class sv_captcha(object):

    def __init__(self, server_url, taskname='', browser=None):
        self.taskname = taskname
        self.page = server_url
        self.cindex = 1
        profile = {'download.default_directory': download_dir}
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_experimental_option('prefs', profile)
        self.browser = browser or webdriver.Chrome( options=chrome_options)

    def startpage(self, checkid=""):
        self.browser.get(self.page)
        linker = self.browser.find_elements_by_xpath(
            '//*[@id="FileSize"]')
        file_size=linker[0].text.split()
        if file_size[1]=='G':
            fo.write(self.page.strip()+' '+str(float(file_size[0])*1024)+'\n')
        else:
            fo.write(self.page.strip()+' '+file_size[0]+'\n')
        fo.flush()

    def close(self):
        self.browser.close()


logging.info("start...")
fp = open('1.txt', encoding='utf8')
lines = fp.readlines()
index = 0
while index != len(lines):
    try:
        yf1 = sv_captcha(lines[index], 'test')
        yf1.startpage('bootyz3')

        index = index+1
    except Exception as e:
        print(e)

    finally:
        yf1.close()
fo.close()


fpp = open('file_size.txt', encoding='utf8')
lines = fpp.readlines()
index = 0
sss={}
while index != len(lines):
    xxx=lines[index].split()
    if xxx[0]  in sss:
        print(xxx[0])
    sss[xxx[0]]=float(xxx[1])

    index = index+1
   
fpp.close()
sss=sorted(sss.items(),key = lambda x:x[1])

print(sss)


if os.path.exists("inordered.txt"):
    foo = open("inordered.txt", mode='a+')
else:
    foo = open("inordered.txt", "w")
for key in sss:   
    foo.write(key[0]+' '+str(key[1])+'\n')
foo.close()
