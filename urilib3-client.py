#!/usr/bin/env python
# coding=utf-8
#!/usr/bin/env python
# coding=utf-8
import ssl
import urllib3
#sudo apt-get install openssl libssl-dev
#urllib3.exceptions.ProxySchemeUnsupported: TLS in TLS requires support for the 'ssl' module
cert_reqs = ssl.CERT_NONE
headers = urllib3.make_headers(proxy_basic_auth='quqi99:password')
proxy = urllib3.ProxyManager('https://quqi.com:3129', proxy_headers=headers, cert_reqs=cert_reqs)
r = proxy.request('GET', 'https://api.snapcraft.io')
print(r.status)

