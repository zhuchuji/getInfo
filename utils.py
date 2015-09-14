#encoding: utf-8
import urllib.request
import http.cookiejar
import urllib.parse
import time
import re
import json
import threading
from queue import Queue
import datetime

threading.stack_size(32768*1000)

#
# 构建简单数据请求和匹配提取，并实现具体请求类提取百度旅游景点数据
# 用浏览器查看百度旅游网站，可知为ajax框架，可直接请求其json数据
# 提取景点的请求类中，使用多线程请求提取，需改进的是应该构造线程池实现并发异步请求，
# 在效率上可带来数量级的提升
# 在本程序中，仅简单通过超时关闭同步请求，缺点是：1.浪费时间，效率很低。2.可能存在数据丢失
# 综合以上两点，本程序需在请求线程处理上改进才能够应用在大量数据提取上
#

#基础类
class Retriever:
    def __init__(self):
        self.header = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.2; WOW64; rv:30.0) Gecko/20100101 Firefox/30.0',
            'Content-Type': 'text/html',
            'Content-Encoding': 'gzip'
        }
        self.cookie = http.cookiejar.CookieJar()
        self.cookie_handler = urllib.request.HTTPCookieProcessor(cookiejar = self.cookie)
        self.opener = urllib.request.build_opener(self.cookie_handler)


    def request(self, url, method, data = None):
        if(data == None):
            return urllib.request.Request(url = url, headers = self.header, method = "GET")
        else:
            return urllib.request.Request(url = url, data = urllib.parse.urlencode(data).encode('utf-8'),
                headers = self.header, method = method)

    def retrieve(self, url, method, data = None):
        response = self.opener.open(self.request(url, method, data)).read().decode('utf-8')
        return response

    def findall(self, html, regexp):
        regexp = re.compile(regexp, re.S)
        result = re.findall(regexp, html)
        return result

    def search(self, html, regexp):
        regexp = re.compile(regexp, re.S)
        result = re.search(regexp, html)
        return result

#多线程请求类
class MultiThreadingFetch(threading.Thread):
    def __init__(self, func, url):
        threading.Thread.__init__(self)
        self.url = url
        self.func = func
        self.result = []

    def run(self):
        self.result += self.func(self.url)

#具体请求类
class RetrieveData(Retriever):
    def __init__(self):
        super().__init__()
        self.data_jingdian = []

    def create_jingdian_url(self, page_num):
        url = "http://lvyou.baidu.com/destination/ajax/jingdian?" +\
                "format=ajax&surl=chongqing&cid=0&pn=" + str(page_num) +\
                "&t=" + str(int(time.time()*1000))
        return url

    def get_jingdian(self, url):
        response = json.loads(self.retrieve(url = url, method = 'GET'))
        scene_list = response['data']['scene_list']
        result = []
        for item in scene_list:
            result.append(item['sname'])
        return result

    def get_jingdian_all(self):
        page_num = 1
        threads = []
        while(page_num <= 31):
            thread = MultiThreadingFetch(func = self.get_jingdian,
                url = (self.create_jingdian_url(page_num)))
            # thread.setDaemon(True)
            threads.append(thread)
            page_num = page_num + 1
            thread.setDaemon(daemonic = True)
            thread.start()

    def print_data_jingdian(self):
        print(self.data_jingdian)
