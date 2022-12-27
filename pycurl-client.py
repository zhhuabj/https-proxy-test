#!/usr/bin/env python
# coding=utf-8
import pycurl
from io import BytesIO
import certifi

def make_pycurl_head(username, password, host, port, target_url='https://api.snapcraft.io', method='HEAD'):
    header_output = BytesIO()
    body_output = BytesIO()
    c = pycurl.Curl()
    c.setopt(pycurl.CAINFO, certifi.where())
    # set proxy-insecure
    c.setopt(c.PROXY_SSL_VERIFYHOST, 0)
    c.setopt(c.PROXY_SSL_VERIFYPEER, 0)
    # set proxy
    c.setopt(pycurl.PROXY, f"https://{host}:{port}")
    # proxy auth
    c.setopt(pycurl.PROXYUSERPWD, f"{username}:{password}")
    # set proxy type = "HTTPS"
    c.setopt(pycurl.PROXYTYPE, 2)
    # target url
    c.setopt(c.URL, target_url)
    c.setopt(pycurl.CUSTOMREQUEST, method)
    c.setopt(pycurl.NOBODY, True)
    c.setopt(c.WRITEDATA, body_output)
    c.setopt(pycurl.HEADERFUNCTION, header_output.write)
    c.setopt(pycurl.HEADERFUNCTION, body_output.write)
    c.setopt(pycurl.CONNECTTIMEOUT, 3)
    c.setopt(pycurl.TIMEOUT, 8)
    return (c, header_output, body_output)

#https://gist.github.com/tumb1er/b7fdf9c257b78d30b6a004149bbd9981
c, header_output, body_output = make_pycurl_head('quqi99', 'password', 'quqi.com', '3129')
c.perform()
status_code = int(c.getinfo(pycurl.HTTP_CODE))
content = body_output.getvalue().decode()
print(status_code)
print(content)
c.close()
