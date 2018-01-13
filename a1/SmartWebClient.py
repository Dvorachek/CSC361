import socket
import ssl
import sys

_BUFF_SIZE = 10000
class smart_web_client(object):
    
    
    def __init__(self, host, port):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.settimeout(10)
        self.s.connect((host, port))
        self.ss = ssl.wrap_socket(self.s, keyfile=None, certfile=None, server_side=False, cert_reqs=ssl.CERT_NONE, ssl_version=ssl.PROTOCOL_SSLv23)
        self.host = host
        self.port = port
        
    def connect(self):
        self.ss.connect((self.host, self.port))
        
    def disconnect(self):
        self.ss.close

    def send_request(self, request):
    
        print request
        self.ss.sendall(request)
        
        response = self.ss.recv(_BUFF_SIZE)
        r = response
        print response

        while response:
            response = self.ss.recv(_BUFF_SIZE)
            r += response
        return r 
        
def main():
    host = "https://www.uvic.ca/"
    host1 = 'github.com'
    host2 = 'www.uvic.ca'
    # h = host.split('/')[2]
    
    port = 80
    port = 443
    # request = b"GET / HTTP/1.0\nHost: {}\r\n\r\n".format(h)

    r1 = "GET / HTTP/1.0\r\nHost: github.com\r\nConnection: close\r\n\r\n"
    
    r2 = "GET / HTTP/1.0\r\nHost: www.uvic.ca\r\nConnection: close\r\n\r\n"

    # try:
    client = smart_web_client(host2, port)
    # except:
        # print "failed creating socket"
    
    # try:
    # client.connect()
    # except:
        # print "failed connecting to {} on {}".format(host, port)
    print 'woop'
    # try:
    response = client.send_request(r2)
    # print response
    print 'test'
    # except Exception, e:
       # print str(e)
    
    # try:
    client.disconnect()
    # except Exception, e:
       # print str(e)


if __name__=='__main__':
    main()

