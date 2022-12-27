#!/usr/bin/env python
# coding=utf-8
import socket, ssl
#MUST use domain if using SNI (ctx.check_hostname=True)
HOST, PORT = 'quqi.com', 7070


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

def handle(conn):
    #https://stackoverflow.com/questions/32792333/python-socket-module-connecting-to-an-http-proxy-then-performing-a-get-request
    #To make a HTTP request to a proxy open a connection to the proxy server
    #and then send a HTTP-proxy request. This request is mostly the same as
    #the normal HTTP request, but contains the absolute URL instead of the relative URL
    #conn.sendall(b'CONNECT api.snapcraft.io:80 HTTP/1.1\r\nHost: api.snapcraft.io\r\n\r\n')
    #print(conn.recv(4096).decode())
    #conn.sendall(b'GET / HTTP/1.1\r\nHost: api.snapcraft.io\r\n\r\n')
    #print(conn.recv(4096).decode())

    #To make a HTTPS request open a tunnel using the CONNECT method and then
    #proceed inside this tunnel normally, that is do the SSL handshake and
    #then a normal non-proxy request inside the tunnel
    conn.sendall(b'CONNECT api.snapcraft.io:443 HTTP/1.1\r\nHost: api.snapcraft.io\r\n\r\n')
    print(conn.recv(4096).decode())                                            
    conn.sendall(b'GET / HTTP/1.1\r\nHost: api.snapcraft.io\r\n\r\n')
    print(conn.recv(4096).decode()) 

    #while True:
        #import rpdb;rpdb.set_trace()
        #it will hang here for the second time because proxy side didn't send so much data yet
    #    data = conn.recv(4096)
    #    print(data.decode())
    #    if not data:
    #        break

def main():
    is_https_proxy = True
    sock = socket.socket(socket.AF_INET)
    if is_https_proxy:
        ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile='/etc/squid/cert/ca.crt')
        ctx.check_hostname = False
        ctx.verify_mode=ssl.CERT_NONE #server side should also use ssl.CERT_NONE
        #ctx.verify_mode = ssl.CERT_REQUIRED
        ctx.load_cert_chain('/etc/squid/cert/quqi.com.crt', '/etc/squid/cert/quqi.com.key')
        #Must use server_hostname to pass SNI if proxy side supports L4 proxy
        wrap = None
        sock = ctx.wrap_socket(sock, server_side=False, server_hostname=HOST)
        #wrap = wrap_socket_via_wrap_bio(ctx, sock, server_side=False, server_hostname=HOST)
    try:
        sock.connect((HOST, PORT))
        if is_https_proxy:
            print("Client requested https-proxy: {}".format(sock.getpeercert()))
        else:
            print("Client requested http-proxy: {}:{}".format(HOST, PORT))
        if wrap:
            handle(wrap)
        else:
            handle(sock)
    finally:
        sock.close()

if __name__ == '__main__':
    main()
