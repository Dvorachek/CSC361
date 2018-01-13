import socket
import ssl
import sys
import re


_BUFF_SIZE = 10000


class smart_web_client(object):

    def __init__(self, host, port):
        # self.secure = self.__check_https(host)
        self.host = host
        self.port = port
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.settimeout(10)
        
        if self.__check_https(host):
            self.__set_https()
            # self.s = ssl.wrap_socket(self.s, keyfile=None, certfile=None, server_side=False, cert_reqs=ssl.CERT_NONE, ssl_version=ssl.PROTOCOL_SSLv23)
        self.connect()
        
    def connect(self):
        self.s.connect((self.host, self.port))
        
    def disconnect(self):
        self.s.close

    def send_request(self, request):
    
        self.s.sendall(request)
        
        response = self.s.recv(_BUFF_SIZE)
        r = response

        while response:
            response = self.s.recv(_BUFF_SIZE)
            r += response
            
        if r:
            return r
        else:
            self.__set_https()
            self.connect()
        
    def __set_https(self):
        self.s = ssl.wrap_socket(self.s, keyfile=None, certfile=None, server_side=False, cert_reqs=ssl.CERT_NONE, ssl_version=ssl.PROTOCOL_SSLv23)
        
    def __check_https(self, host):
        return True
        print host
        if re.match(r"https://.+", host):
            
            print 'yes'
            return True
        print 'no'
        return False


def main():
    host = sys.argv[1]
    #TESTS
    host1 = 'github.com'
    host2 = 'www.uvic.ca'
    request1 = "HEAD / HTTP/1.0\r\nHost: github.com\r\nConnection: close\r\n\r\n"
    request2 = "HEAD / HTTP/1.0\r\nHost: www.uvic.ca\r\nConnection: close\r\n\r\n"

    port = 80
    port = 443

    request = "HEAD / HTTP/1.0\r\nHost: {}\r\nConnection: close\r\n\r\n".format(host)

    client = smart_web_client(host, port)

    response = client.send_request(request)
    
    if not response:
        client.__set_https()
        client.connect()
        response = client.send_request(request)
        
    print response
    
    # response = response.split(' ')[1]

    print 'end'

    client.disconnect()


if __name__=='__main__':
    main()
