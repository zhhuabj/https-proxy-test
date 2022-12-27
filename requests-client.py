#!/usr/bin/env python
# coding=utf-8
import requests
proxies = {'https': 'https://quqi.com:7070'}
r=requests.get("https://api.snapcraft.io", proxies=proxies)
print(r.text)
