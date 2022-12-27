#!/usr/bin/env python
# coding=utf-8
import ssl
import socket
from urllib import request
import http.client

class TLSProxyConnection(http.client.HTTPSConnection):
    """Like HTTPSConnection but more specific"""
    def __init__(self, host, **kwargs):
        http.client.HTTPSConnection.__init__(self, host, **kwargs)

    def connect(self):
        print('socket:%s:%s' % (self.host, self.port))
        sock = socket.create_connection((self.host, self.port),
                self.timeout, self.source_address)
        if getattr(self, '_tunnel_host', None):
            self.sock = sock
            print(self.sock)
            #import rpdb;rpdb.set_trace()
            ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile='/etc/squid/cert/ca.crt')
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            ctx.load_cert_chain('/etc/squid/cert/quqi.com.crt', '/etc/squid/cert/quqi.com.key')
            self.sock = ctx.wrap_socket(sock, server_side=False, server_hostname=self.host)
            print(self.sock)
            self._tunnel()

class TLSProxyHandler(request.HTTPSHandler):
    def __init__(self, proxies=None):
        request.HTTPSHandler.__init__(self)

    def https_open(self, req):
        return self.do_open(TLSProxyConnection, req)


proxy_handler = request.ProxyHandler({"https": "https://quqi.com:7070"})
opener = request.build_opener(proxy_handler, TLSProxyHandler())
req = request.Request("http://api.snapcraft.io", method="GET")
request.install_opener(opener)
with opener.open(req) as f:
    print(f.read().decode('utf-8'))
print('ok')
