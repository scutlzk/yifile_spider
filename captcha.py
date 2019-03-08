#!/usr/bin/env python
# -*- coding: utf8

import os
from PIL import Image
from PIL import ImageFilter
from PIL import ImageEnhance

class captcha(object):

    # load a captcha pic file and optimize output
    def __init__(self, imgfile):
        assert os.path.exists(imgfile)
        self.path = imgfile
        self.imf = Image.open(self.path)

    def __binarizing(self, threshold):
        pixdata = self.imf.load()
        w,h = self.imf.size
        for j in xrange(h):
            for i in xrange(w):
                if pixdata[i, j] < threshold:
                    pixdata[i, j] = 0
                else:
                    pixdata[i, j] = 255
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

    def __sp_png(self):
        # work with yifile
        if self.imf.mode != 'P':
            print "file not P mode with a palette"
            return None
        pixdata = self.imf.load()
        w, h = self.imf.size
        for j in xrange(h):
            for i in xrange(w):
                if pixdata[i, j] == 2:
                    pixdata[i, j] = 0

    def __png_cut_scratch(self):
        # sumup the first/second used palette index[first: background(white), second(scratch)]
        # convert second to first
        if self.imf.mode != 'P':
            raise RuntimeError("file not P mode with a palette")
        pmax = 20
        pixdata = self.imf.load()
        # take 20, index0 - 19
        palette = [0] * pmax
        m = 0
        w, h = self.imf.size
        for j in xrange(h):
            for i in xrange(w):
                m = pixdata[i, j]
                if m < pmax:
                    palette[m] += 1
        f = max(palette)
        for i in xrange(len(palette)):
            if palette[i] == f:
                palette[i] = 0
                break
        s = max(palette)
        print f,s
        for j in xrange(h):
            for i in xrange(w):
                m = pixdata[i, j]
                if m == s:
                    pixdata[i, j] = f

    def optimize(self, outname=''):
        if self.path.endswith('png') and self.__sp_png():
            pass
        else:
            self.imf = self.imf.filter(ImageFilter.MedianFilter(1))  #对于输入图像的每个像素点，该滤波器从（size，size）的区域中拷贝中值对应的像素值存储到输出图像中
            self.imf = ImageEnhance.Contrast(self.imf).enhance(1.5) #enhance()的参数factor决定着图像的对比度情况。从0.1到0.5，再到0.8，2.0，图像的对比度依次增大.0.0为纯灰色图像;1.0为保持原始
            self.imf = self.imf.convert('L')   #灰度图转换
            self.__denoising()
            self.__binarizing(200)
        outname = outname or self.path
        self.imf.save(outname)