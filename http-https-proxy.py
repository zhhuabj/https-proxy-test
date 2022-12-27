#!/usr/bin/env python
# coding=utf-8
import ssl
import socket
import _thread
 
#https://raw.githubusercontent.com/python-trio/trio/master/notes-to-self/ssl-handshake/ssl-handshake.py
class ManuallyWrappedSocket:
    def __init__(self, ctx, sock, **kwargs):
        self.incoming = ssl.MemoryBIO()
        self.outgoing = ssl.MemoryBIO()
        self.obj = ctx.wrap_bio(self.incoming, self.outgoing, **kwargs)
        self.sock = sock

    def _retry(self, fn, *args):
        finished = False
        while not finished:
            want_read = False
            try:
                ret = fn(*args)
            except ssl.SSLWantReadError:
                want_read = True
            except ssl.SSLWantWriteError:
                # can't happen, but if it did this would be the right way to
                # handle it anyway
                pass
            else:
                finished = True
            # do any sending
            data = self.outgoing.read()
            if data:
                self.sock.sendall(data)
            # do any receiving
            if want_read:
                data = self.sock.recv(4096)
                if not data:
                    self.incoming.write_eof()
                else:
                    self.incoming.write(data)
            # then retry if necessary
        return ret

    def do_handshake(self):
        self._retry(self.obj.do_handshake)

    def recv(self, bufsize):
        return self._retry(self.obj.read, bufsize)

    def sendall(self, data):
        self._retry(self.obj.write, data)

    def unwrap(self):
        self._retry(self.obj.unwrap)
        return self.sock


def wrap_socket_via_wrap_bio(ctx, sock, **kwargs):
    return ManuallyWrappedSocket(ctx, sock, **kwargs)


class Header:
 
    def __init__(self, conn):
        self._method = None
        header = b''
        try:
            while 1:
                data = conn.recv(4096)
                header = b"%s%s" % (header, data)
                if header.endswith(b'\r\n\r\n') or (not data):
                    break
        except Exception as err:
            print('__init__: ', err)
            pass
        self._header = header
        self.header_list = header.split(b'\r\n')
        self._host = None
        self._port = None
 
    def get_method(self):
        if self._method is None:
            self._method = self._header[:self._header.index(b' ')]
        return self._method
 
    def get_host_info(self):
        if self._host is None:
            method = self.get_method()
            line = self.header_list[0].decode('utf8')
            if method == b"CONNECT":
                host = line.split(' ')[1]
                if ':' in host:
                    host, port = host.split(':')
                else:
                    port = 443
            else:
                for i in self.header_list:
                    if i.startswith(b"Host:"):
                        host = i.split(b" ")
                        if len(host) < 2:
                            continue
                        host = host[1].decode('utf8')
                        break
                else:
                    host = line.split('/')[2]
                if ':' in host:
                    host, port = host.split(':')
                else:
                    port = 80
            self._host = host
            self._port = int(port)
        return self._host, self._port
        #return '185.125.188.58', 443
 
    @property
    def data(self):
        return self._header
 
    def is_ssl(self):
        if self.get_method() == b'CONNECT':
            return True
        return False
 
    def __repr__(self):
        return str(self._header.decode("utf8"))
 
def communicate(sock1, sock2):
    try:
        while 1:
            data = sock1.recv(1024)
            if not data:
                return
            sock2.sendall(data)
    except Exception as err:
        print(sock1)
        #for http over https proxy: <socket.socket fd=6, family=AddressFamily.AF_INET, type=SocketKind.SOCK_STREAM, proto=0, laddr=('192.168.99.186', 48246), raddr=('185.125.188.54', 80)>
        #for https over https proxy: <socket.socket fd=6, family=AddressFamily.AF_INET, type=SocketKind.SOCK_STREAM, proto=0, laddr=('192.168.99.186', 47916)>
        print('communicate: ', err)
        pass
 
 
def handle(client, isbio=False):
    timeout = 60
    if not isbio:
        client.settimeout(timeout)
    try:
        header = Header(client)
        print(header)
        if not header.data:
            return
        print(*header.get_host_info(), header.get_method())
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print('connecting to target: %s', header.get_host_info())
        server.connect(header.get_host_info())
        #如果这里加密了，https over https proxy时不会报错，但client将也看不到这里加密的内容哦
        #ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        #ctx.check_hostname = True
        #ctx.verify_mode=ssl.CERT_NONE
        #server = ctx.wrap_socket(server, server_side=False)
        server.settimeout(timeout)
        use_nio = False
        if header.is_ssl():
            data = b"HTTP/1.0 200 Connection Established\r\n\r\n"
            client.sendall(data)
            print('-------------------client -> target')
            print(client)
            print(server)
            if not use_nio:
                _thread.start_new_thread(communicate, (client, server))
        else:
            server.sendall(header.data)
        print('-------------------target -> client:')
        print(server)
        print(client)
        if not use_nio:
            communicate(server, client)
        else:
            fdset = [clientSock, serverSock]
            while not stop:
                r, w, e = select.select(fdset, [], [], 5)
                if clientSock in r:
                    if serverSock.send(clientSock.recv(1024)) <= 0: break
                if serverSock in r:
                    if clientSock.send(serverSock.recv(1024)) <= 0: break 
    except:
        server.close()
        if not isbio:
            client.close()
 
 
def serve(ip, port, is_https_proxy):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((ip, port))
    s.listen(10)
    print('proxy start...')
    if is_https_proxy:
        ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH, cafile='/etc/squid/cert/ca.crt')
        #ctx.verify_mode = ssl.CERT_REQUIRED
        ctx.verify_mode=ssl.CERT_NONE
        ctx.load_cert_chain('/etc/squid/cert/quqi.com.crt', '/etc/squid/cert/quqi.com.key')
        ctx.load_verify_locations(cafile='/etc/squid/cert/ca.crt')
    while True:
        #import rpdb;rpdb.set_trace()
        client, addr = s.accept()
        print("Client connected: {}:{}".format(addr[0], addr[1]))
        if is_https_proxy:
            client = ctx.wrap_socket(client, server_side=True, do_handshake_on_connect=False)
            client.do_handshake()
            wrap = None
            #wrap = wrap_socket_via_wrap_bio(ctx, client, server_side=True)
            #getpeeercert will be empty if it is verify_mode=ssl.CERT_NONE
            print("SSL established. Peer: {}".format(client.getpeercert()))
        if(wrap):
            _thread.start_new_thread(handle, (wrap, True))
        else:
            _thread.start_new_thread(handle, (client, False))
 
 
stop = False
if __name__ == '__main__':
    #HTTP Proxy:  curl --resolve quqi.com:7070:127.0.0.1 -x http://quqi.com:7070 http://api.snapcraft.io:80
    #             curl --resolve quqi.com:7070:127.0.0.1 -x http://quqi.com:7070 https//api.snapcraft.io:443
    #HTTPS Proxy: curl --resolve quqi.com:7070:127.0.0.1 --proxy-cacert /etc/squid/cert/ca.crt -x https://quqi.com:7070 https://api.snapcraft.io:443
    #             curl --resolve quqi.com:7070:127.0.0.1 --proxy-cacert /etc/squid/cert/ca.crt -x https://quqi.com:7070 http://api.snapcraft.io:80
    is_https_proxy = True
    IP = "127.0.0.1"
    PORT = 7070
    serve(IP, PORT, is_https_proxy)
    try:                                                                        
        input('Enter any key to stop.\r\n')                                     
    finally:                                                                    
        stop = True
