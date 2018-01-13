import socket
import ssl
import sys

_BUFF_SIZE = 10000
class smart_web_client(object):
    
    
    def __init__(self, host, port):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ss = ssl.wrap_socket(self.s, ssl_version=ssl.PROTOCOL_TLSv1)
        self.host = host
        self.port = port
        
    def connect(self):
        self.ss.connect((self.host, self.port))
        
    def disconnect(self):
        self.ss.close

    def send_request(self, request):
        print request
        self.ss.send(request)
        response = self.ss.recv(_BUFF_SIZE)
        r = response
        print response
        
        
        t = response
        while response:
            response = self.ss.recv(_BUFF_SIZE)
            r += response
        return r 
        
def main():
    host = "https://www.uvic.ca/"
    h = host.split('/')[2]
    
    port = 80
    request = b"GET / HTTP/1.0\nHost: {}\r\n\r\n".format(h)
    
    
    
    r2 = b"GET / HTTP/1.0\nHost: uvic.ca\n\n"

    # try:
    client = smart_web_client(h, port)
    # except:
        # print "failed creating socket"
    
    # try:
    client.connect()
    # except:
        # print "failed connecting to {} on {}".format(host, port)
    
    # try:
    response = client.send_request(request)
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

