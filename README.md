# yifile_spider
fork from https://github.com/alexsumsher/yifile_spider

A Spider collecting download url from yifile server。 works with selenium and pyocr-tesseract.

把网址放到1.txt里面，然后代码里修改下载路径download_dir，tesseract路径tes_path 就能自动下载网址里的zip文件。

新增order_filesize.py 会将1.txt里的url 按照文件大小排序 生成inordered.txt。可以将inordered.txt 复制到 1.txt,就可以按照文件大小下载文件