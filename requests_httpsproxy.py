#!/usr/bin/env python
# coding=utf-8
import requests
import requests_httpsproxy
https_proxy = 'https://quqi.com:7070'
sess = requests.Session()
print(sess.get('https://httpbin.org/ip', proxies={'http':https_proxy, 'https':https_proxy}).text)
