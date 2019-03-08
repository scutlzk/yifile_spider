#!/usr/bin/env python
# -*- coding: utf8
#
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

import requests
import logging

logging.basicConfig(level=logging.DEBUG, format='(%(funcName)-10s) %(message)s')
cur_path = os.getcwd()

# initial environment
tes_path = 'D:\\Programs\\tesseract-ocr'
tph = tes_path + ';' + os.getenv('PATH')
os.environ['PATH'] = tph
os.environ['TESSDATA_PREFIX'] = tes_path

import pyocr
import pyocr.builders

#sys._MEIPASS = 'D:\\Programs\\tesseract-ocr'
#sys.frozen = True
"""
Tesseract可以被赋予一个页面模式参数（-psm），它可以有以下值：

0 =方向和脚本检测（OSD）。
1 =使用OSD自动分页。
2 =自动分页，但没有OSD或OCR
3=全自动页面分割，但没有OSD。（默认）
4 =假设一列可变大小的文本。
5 =假定一个统一的垂直排列文本块。
6 =假设一个统一的文本块。
7 =将图像视为单个文本行。
8 =将图像视为一个单词。
9 =将图像视为一个圆圈中的单个单词。
10 =将图像视为单个字符。
"""

# check ocr
def ocr_checker():
    #print os.environ['PATH']
    tools = pyocr.get_available_tools()
    if len(tools) == 0:
        return None
    for t in tools:
        tn = t.get_name()
        if tn.startswith('Tesseract'):
            return t
    return None

def some_try(tes):
    lis = tes.image_to_string(Image.open(os.path.join(cur_path, 'cp1.PNG')), lang='eng', builder=pyocr.builders.LineBoxBuilder())
    # box = pyocr.builders.LineBoxBuilder()=>box.tesseract_flags[1](psm) = "7"....
    return lis

def do_ocr(tool, img):
    bdl = pyocr.builders.TextBuilder()
    bdl.tesseract_flags[1] = "7"
    if isinstance(img, (str, unicode)):
        img = Image.open(img)
    return tool.image_to_string(img, lang='eng', builder=bdl)


def yifile_png(im):
    # work with yifile(yifile vcode png: noise scratch color's index set to background's index(2->0))
    if im.mode != 'P':
        logging.error("file not P mode with a palette")
        return None
    pixdata = im.load()
    w, h = im.size
    for j in xrange(h):
        for i in xrange(w):
            if pixdata[i, j] == 2:
                pixdata[i, j] = 0
    return im


class captcha(object):
    basedir = os.getcwd()

    # load a captcha pic file and optimize output
    def __init__(self, imgfile):
        if isinstance(imgfile, (str, unicode)):
            assert os.path.exists(imgfile)
            self.path = imgfile
            self.imf = Image.open(self.path)
        elif hasattr(imgfile, 'size'):
            self.imf = imgfile
            self.path = ""
        else:
            raise ValueError("Not Correct Input.")

    def __binarizing(self, threshold):
        pixdata = self.imf.load()
        w,h = self.imf.size
        for j in range(h):
            for i in range(w):
                if pixdata[i,j]<threshold:
                    pixdata[i,j]=0
                else:
                    pixdata[i,j]=255
        return True

    def __denoising(self):
        pixdata = self.imf.load()
        w,h = self.imf.size
        for j in range(1, h-1):
            for i in range(1, w-1):
                count = 0
                if pixdata[i, j-1] > 245:
                    count = count + 1
                if pixdata[i, j+1] > 245:
                   count = count + 1
                if pixdata[i+1, j] > 245:
                    count = count + 1
                if pixdata[i-1, j] > 245:
                    count = count + 1
                if count > 2:
                    pixdata[i, j]=255

    def optimize(self, outname=''):
        if self.path.endswith('png') and self.__sp_png():
            pass
        else:
            self.imf = self.imf.filter(ImageFilter.MedianFilter(1))  #对于输入图像的每个像素点，该滤波器从（size，size）的区域中拷贝中值对应的像素值存储到输出图像中
            self.imf = ImageEnhance.Contrast(self.imf).enhance(1.5) #enhance()的参数factor决定着图像的对比度情况。从0.1到0.5，再到0.8，2.0，图像的对比度依次增大.0.0为纯灰色图像;1.0为保持原始
            self.imf = self.imf.convert('L')   #灰度图转换
            self.__denoising()
            self.__binarizing(200)
        if outname or self.path:
            self.imf.save(outname or self.path)
        return self.imf


class sv_captcha(object):
    workdir = ''

    def __init__(self, server_url, taskname='', browser=None):
        self.taskname = taskname
        self.page = server_url
        self.cindex = 1
        self.browser = browser or webdriver.Chrome()

    def startpage(self, checkid=""):
        self.browser.get(self.page)
        if checkid:
            w = WDW(self.browser, 30)
            w.until(EC.presence_of_element_located((By.ID, checkid)))
        else:
            w = None
            time.sleep(30)
        return True

    def get_captcha(self):
        raise NotImplementedError

    def take_img(self, url, savefile=""):
        if not isinstance(url, (str, unicode)):
            return None
        try:
            r = requests.get(url, timeout=5)
        except requests.exceptions.Timeout:
            logging.warning("time out to get: %s" % url)
            return None
        if savefile:
            try:
                f = open(savefile, 'wb')
                f.write(r.content)
                f.close()
            except IOError:
                logging.warning("Write image file (%s) Error!" % savefile)
        im = Image.open(BytesIO(r.content))
        return im

    def close(self):
        self.browser.close()


class yifile(sv_captcha):
    workdir = cur_path
    baseurl = 'https://www.yifile.com'

    def __prepare(self):
        # A Block of 30s from server, even we set downtime=0, still have to wait for 30s...
        try:
            self.browser.execute_script('startWait()')
        except selenium.common.exceptions.JavascriptException:
            time.sleep(1)
            start_btn = self.browser.find_elements_by_class_name("newfdown")
            start_btn = start_btn[0] if isinstance(start_btn, list) else start_btn
            start_btn.click()
        #start_btn = self.browser.find_element_by_xpath('//*[@id="FVIEW"]/div[3]/table/tbody/tr[4]/td[2]/a')
        time.sleep(29)
        checker = self.browser.find_elements_by_id('bootyz3')
        checker = checker[0] if isinstance(checker, list) else checker
        for x in xrange(10):
            if checker.is_displayed():
                return True
            time.sleep(0.5)
        #self.browser.execute_script('startWait()')
        self.browser.execute_script('document.getElementById("bootyz1").style.display="block"')
        self.browser.execute_script('document.getElementById("bootyz2").style.display="block"')
        self.browser.execute_script('document.getElementById("bootyz3").style.display="block"')
        return True

    def __sendcode(self, keys):
        self.browser.execute_script('document.getElementById("verycode").value="%s"' % keys)
        self.browser.execute_script('downboot()')
        try:
            w = WDW(self.browser, 3)
            r = w.until(EC.alert_is_present())
            logging.info(r.text)
            r.accept()
            # when alert: auto refresh vcode
            return False
        except selenium.common.exceptions.TimeoutException:
            # no alert
            return True

    def __getlink(self):
        linker = self.browser.find_elements_by_xpath('//*[@id="FVIEW"]/div[3]/table/tbody/tr[4]/td[2]/span[2]/a')
        if not linker:
            linker = self.browser.find_elements_by_class_name("fdown1")
        if not linker:
            logging.error("no linker found!")
            return ""
        linker = linker[0] if isinstance(linker, list) else linker
        url = linker.get_attribute('href')
        # //*[@id="FVIEW"]/div[3]/table/tbody/tr[4]/td[2]/span[2]/a
        # document.getElementsByClassName("fdown1")
        logging.info('get linke url: %s' % url)
        return url

    def get_captcha(self, limit=0):
        limit = limit or 10
        assert self.__prepare()
        imgcode = self.browser.find_elements_by_id('imgcode')
        if isinstance(imgcode, list):
            imgcode = imgcode[0]
        time.sleep(1)
        tool = ocr_checker()
        logging.info(str(imgcode))
        for _ in xrange(limit):
            u = imgcode.get_attribute('src')
            logging.info(u)
            if not u:
                time.sleep(1)
                continue
            im = Image.open(BytesIO(imgcode.screenshot_as_png))
            # <img />: screenshot_as_png property png data
            imgf = os.path.join(cur_path, self.taskname + str(self.cindex) + '.png')
            #r = requests.get(u)
            #im = Image.open(BytesIO(r.content))
            #im = yifile_png(im)
            #with open(imgf, 'wb') as f:
            #    f.write(im)
            im = captcha(im).optimize()
            vcode = do_ocr(tool, im)
            logging.info("a vcode ocr by: %s" % vcode)
            if len(vcode) == 4 and vcode.isalnum():
                logging.info("got a vcode: %s" % vcode)
                im.save(vcode + '.png')
                if self.__sendcode(vcode):
                    return self.__getlink()
            else:
                im.save(imgf)
                imgcode.click()
            im.close()
            time.sleep(0.1)
            self.cindex += 1


if __name__ == '__main__':
    logging.info("start...")
    yf1 = yifile('https://www.yifile.com/file/UYf6f3eXxl/VjhAW7GG9.html', 'test')
    yf1.startpage('bootyz3')
    yf1.get_captcha(11)
    yf1.close()
