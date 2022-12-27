#!/usr/bin/env python
# coding=utf-8
import tlslite, ssl, socket
sock = tlslite.TLSConnection(socket.create_connection(('127.0.0.1', 7070)))
sock.handshakeClientCert()
sock.sendall(bytes('CONNECT api.snapcraft.io:443 HTTP/1.1\r\nHost: api.snapcraft.io:443\r\n\r\n', 'ascii'))
sock.recv(1024)

conn = tlslite.TLSConnection(sock)
conn.handshakeClientCert()
conn.sendall(b'GET / HTTP/1.1\r\nHost: api.snapcraft.io\r\n\r\n')
print(conn.recv(1024).decode())
