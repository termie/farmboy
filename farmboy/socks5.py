

"""An HTTP proxy that speaks SOCKS5 on the backend that can be run in-process.

The purpose of this is so that we can point at a proxy set up by a command
like `ssh -D mygatewayserver` when we do python HTTP_PROXY calls.

It is a limited implementation.

"""

# A bunch of this is based on https://code.google.com/p/socksipy-branch,
# one of many seemingly abandoned projects for dealing with SOCKS

import BaseHTTPServer
import httplib
import os
import socket
import StringIO
import struct
import threading

from fabric.api import env
from fabric.api import task

env.farmboy_socks_proxy = os.environ.get('SOCKS_PROXY', 'localhost:1080')


class Socks5Socket(socket.socket):
  HELO = struct.pack('BBB', 0x05, 0x01, 0x00)
  SETD = struct.pack('BBB', 0x05, 0x01, 0x00)

  def __init__(self, rdns=True):
    self.rdns = rdns
    socket.socket.__init__(
        self, family=socket.AF_INET, type=socket.SOCK_STREAM, proto=0)

  def recvall(self, count):
    data = self.recv(count)
    while len(data) < count:
      d = self.recv(count - len(data))
      if not d:
        raise Exception('connection closed unexpectedly')
      data = data + d
    return data

  def negotiate(self):
    self.sendall(self.HELO)

    chosenauth = self.recvall(2)
    if chosenauth[0] != '\x05':
      self.close()
      raise Exception('invalid data received: ' + repr(chosenauth))

    if chosenauth[1] != '\x00':
      raise NotImplemented('only no-auth is implemented: ' + repr(chosenauth))

  def set_destination(self, addr, port):
    req = self.SETD

    # If the given destination address is an IP address, we'll
    # use the IPv4 address request even if remote resolving was specified.
    try:
      ipaddr = socket.inet_aton(addr)
      req = req + '\x01' + ipaddr
    except socket.error:
      if self.rdns:
        # Resolve remotely
        ipaddr = None
        req = req + '\x03' + chr(len(addr)).encode() + addr.encode()
      else:
        # Resolve locally
        ipaddr = socket.inet_aton(socket.gethostbyname(addr))
        req = req + '\x01' + ipaddr

    req = req + struct.pack('>H', int(port))
    self.sendall(req)

    # Alright, let's see if that worked out
    resp = self.recvall(4)
    if resp[0] != '\x05':
      # we got something weird back
      sock.close()
      raise Exception('invalid data')
    elif resp[1] != '\x00':
      # connection failed
      self.close()
      raise Exception('connection failed: ' + repr(resp))
    elif resp[3] == '\x01':
      boundaddr = self.recvall(4)
    elif resp[3] == '\x03':
      resp = resp + self.recv(1)
      boundaddr = self.recvall(ord(resp[4]))
    else:
      self.close()
      raise Exception('invalid data: ' + repr(resp))

    boundport = struct.unpack('>H', self.recvall(2))[0]

    # NOTE(termie): None of my tests produced values for boundaddr and
    #               boundport that we needed to care about


class SocketSaver(object):
  def __init__(self, sock):
    self._sock = sock
    self._raw = StringIO.StringIO()
    self._fp = None

  def makefile(self, *args, **kw):
    self._fp = self._sock.makefile(*args, **kw)
    return self

  def read(self, *args, **kw):
    rv = self._fp.read(*args, **kw)
    self._raw.write(rv)
    return rv

  def readline(self, *args, **kw):
    rv = self._fp.readline(*args, **kw)
    self._raw.write(rv)
    return rv

  def getvalue(self):
    return self._raw.getvalue()

  def __getattr__(self, key):
    return getattr(self._fp, key)


class HttpToSocks5Factory(object):
  def __init__(self, addr, port):
    self.addr = addr
    self.port = port

  def __call__(self, *args, **kw):
    return HttpToSocks5Handler(self.addr, self.port, *args, **kw)


class HttpToSocks5Handler(BaseHTTPServer.BaseHTTPRequestHandler):
  def __init__(self, addr, port, *args, **kw):
    self.addr = addr
    self.port = port
    BaseHTTPServer.BaseHTTPRequestHandler.__init__(self, *args, **kw)

  def _rebuild_request(self):
    raw = self.raw_requestline + str(self.headers) + '\r\n'
    content_length = self.headers.get('Content-Length', 0)
    content = self.rfile.read(int(content_length))
    raw = raw + content
    return raw

  def _get_destination(self):
    host_header = self.headers.get('Host')
    parts = host_header.split(':')
    host = parts.pop(0)
    if parts:
      port = parts.pop(0)
    else:
      port = 80

    return host, port

  def do_SOCKS5(self):
    sock = Socks5Socket()
    sock.connect((self.addr, int(self.port)))
    sock.negotiate()

    # Figure out where we want to send the request
    host, port = self._get_destination()
    sock.set_destination(host, port)

    # Send the request through the proxy
    req = self._rebuild_request()
    sock.sendall(req)

    # Get the response
    buf = SocketSaver(sock)
    http_resp = httplib.HTTPResponse(buf)
    http_resp.begin()
    http_resp.read()

    resp = buf.getvalue()
    self.wfile.write(resp)

  do_GET = do_SOCKS5
  do_POST = do_SOCKS5
  do_HEAD = do_SOCKS5
  do_PUT = do_SOCKS5


def _real_serve(server, event):
  while not event.is_set():
    server.handle_request()


def serve(http_addr, http_port, proxy_addr, proxy_port):
  event = threading.Event()
  server = BaseHTTPServer.HTTPServer(
      (http_addr, http_port), HttpToSocks5Factory(proxy_addr, proxy_port))

  thread = threading.Thread(target=_real_serve, args=(server, event))
  thread.daemon = True
  thread.start()
  return event


@task
def proxy(host=None, port=None):
  if host is None:
    host, port = env.farmboy_socks_proxy.split(':')

  os.environ['HTTP_PROXY'] = 'http://localhost:1081'
  evt = serve('localhost', 1081, host, port)

