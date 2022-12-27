#!/usr/bin/env python
# coding=utf-8
try: 
    import http.client as httplib
    import base64
    #c = httplib.HTTPSConnection('quqi.com', 3129)
    c = httplib.HTTPConnection('quqi.com', 7070)
    headers = {}
    #auth = base64.b64encode(b"quqi99:password").decode("utf-8")
    #headers['Proxy-Authorization'] = f'Basic ' + base64.b64encode(auth)
    #c.set_tunnel('api.snapcraft.io', 443, headers={"Proxy-Authorization": f"Basic {auth}"}) 
    c.set_tunnel('api.snapcraft.io', 443, headers=headers) 
    c.request('HEAD', '/') 
    res = c.getresponse() 
    print(res.status, res.reason) 
except Exception as err: 
    print(err)
