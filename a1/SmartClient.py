import socket
import ssl
import sys
import h2.connection


_BUFF_SIZE = 10000
http_version = ''
https = ''

# A class for connecting of a specified host
class smart_web_client(object):
    def __init__(self, host):  # Constructor
        self.host = host
        self.port = 80
        self.secure_port = 443
        
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ss = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.__set_https()  # wrap the https socket
        self.__connect()  # attempt connecting to both sockets
    
    def send_request(self):
        request = str.encode("HEAD / HTTP/1.1\r\nHost: {}\r\nConnection: close\r\n\r\n".format(self.host))  # encode string to byte array
        
        response = []  # the responses are stored in a list
        response.append(send_http_request(self.ss, request))
        response.append(send_http_request(self.s, request))
        
        # response_ok returns the index of the chosen reponse.. Python evaluates right to left
        return response[response_ok(response)]
    
    def disconnect(self):  # Fairly straight forward
        try:
            self.s.close
        except:
            print('no http connection to disconnect')
        
        try:
            self.ss.close
        except:
            print('no https connection to disconnect')
    
    # Sets timeouts and connects to both http and https
    def __connect(self):
        self.s.settimeout(10)
        self.ss.settimeout(10)
        try:
            self.s.connect((self.host, self.port))
        except:
            print('http failed')
        
        try:
            self.ss.connect((self.host, self.secure_port))
        except:
            print('https failed')
    
    # SSL wraps the secure socket for https
    def __set_https(self):
        self.ss = ssl.wrap_socket(self.ss, keyfile=None, certfile=None, server_side=False, cert_reqs=ssl.CERT_NONE, ssl_version=ssl.PROTOCOL_SSLv23)

# Takes a socket and request as a parameter and returns the response
def send_http_request(sock, request):
    sock.sendall(request)
    response = sock.recv(_BUFF_SIZE)
    r = response

    while response:
        response = sock.recv(_BUFF_SIZE)
        r += response
        
    return r.decode()  # need to decode the byte array to string
        
# Parses the response code from the response header
def response_code(response):
    response = response.split(' ')
    return response[1]

# Parses the redirection location from the response header in case of 301 or 302
def locate(response):
    response = response.split('\n')
    location = ''
    for line in response:
        if line[:10] == 'Location: ':
            location = line[10:]
            break
    
    return location

# Follows the redirection by connecting to the parsed resource
def redirection(location):
    global https
    location = location.strip().strip('/')
    
    if location[:8] == 'https://':
        location = location[8:]
        https = 'yes'
    elif location[:7] == 'http://':
        location = location[7:]
        https = 'no'
        
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(10)
    
    if https == 'yes':
        try:
            sock.connect((location, 443))
            sock = ssl.wrap_socket(sock, keyfile=None, certfile=None, server_side=False, cert_reqs=ssl.CERT_NONE, ssl_version=ssl.PROTOCOL_SSLv23)
        except:
            print("Failed to resolve host IP and connect to socket.\n" +
                   "Redirection failed on https at {}. Likely 503 Error.".format(location)
                 )
            exit(1)
    else:
        try:
            sock.connect((location, 80))
        except:
            print("Failed to resolve host IP and connect to socket.\n" +
                   "Redirection failed on http at {}. Likely 503 Error.".format(location)
                 )
            exit(1)
        
    request = str.encode("HEAD / HTTP/1.0\r\nHost: {}\r\nConnection: close\r\n\r\n".format(location))  # encode string to byte array
    sock.sendall(request)
    response = sock.recv(_BUFF_SIZE)
    sock.close
    return response.decode()  # need to decode the byte array to string

# Returns the index of the response within the "response" list that should be used
# If the response is 404 or 505, then error is reported and program exits
def response_ok(response):
    global https
    
    if response_code(response[0]) == '200':
        https = 'yes'
        return 0
    elif response_code(response[1]) == '200':
        https = 'no'
        return 1
    elif response_code(response[0]) in '301 302':
        response.append(redirection(locate(response[0])))
        return 2
    elif response_code(response[1]) in '301 302':
        response.append(redirection(locate(response[0])))
        return 2
    elif response_code(response[0]) in '404' or response_code(response[1]) in '404':
        print("404 Error, client was able to communicate with server, but resource was not located")
        exit(1)
    elif response_code(response[0]) in '505' or response_code(response[1]) in '505':
        print("505 Error, HTTP version not supported")
        exit(1)
        
# Parses cookie information from header and prints everything specified by assignment
def parse_and_format(response, host):
    global http_version, https

    response = response.split('\n')

    cookies = []
    for item in response:
        if 'HTTP' in item and not http_version:
            http_version = item.split(' ')[0]
        if 'Set-Cookie:' in item:
            cookies.append(item[11:])

    print("\nwebsite: {}".format(host))
    print("1. Support of HTTPS: {}".format(https))
    print("2. The newest HTTP versions that the web server supports: {}".format(http_version))
    print("3. List of Cookies:")

    for item in cookies:
        name = '-'
        key = '-'
        domain = host
        item = item.split(';')
        key = item[0].split('=')[0]
        for segment in item:
            if 'domain' in segment:
                domain = segment.split('=')[1]

        print("name: {}, key: {}, domain name: {}".format(name, key, domain))

# The next THREE functions were taken from: https://python-hyper.org/projects/h2/en/stable/negotiating-http2.html
# The purpose is to determine if the server supports HTTP2
# Comments have been removed to make functions smaller, but can be recovered by following the above link
def establish_tcp_connection(host):
    return socket.create_connection((host, 443))

def get_http2_ssl_context():
    ctx = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH)
    ctx.options |= (
        ssl.OP_NO_SSLv2 | ssl.OP_NO_SSLv3 | ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1
    )
    ctx.options |= ssl.OP_NO_COMPRESSION
    ctx.set_ciphers("ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20")
    ctx.set_alpn_protocols(["h2", "http/1.1"])

    try:
        ctx.set_npn_protocols(["h2", "http/1.1"])
    except NotImplementedError:
        pass

    return ctx
    
def negotiate_tls(tcp_conn, context, host):
    global http_version
    tls_conn = context.wrap_socket(tcp_conn, server_hostname=host)

    negotiated_protocol = tls_conn.selected_alpn_protocol()
    if negotiated_protocol is None:
        negotiated_protocol = tls_conn.selected_npn_protocol()

    if negotiated_protocol != "h2":
        print("Didn't negotiate HTTP/2!")
    else:
        http_version = 'HTTP/2'

    return tls_conn

def check_http2(host):
    context = get_http2_ssl_context()
    connection = establish_tcp_connection(host)
    tls_connection = negotiate_tls(connection, context, host)


def main():
    if len(sys.argv) < 2:
        print("Invalid program usage, please specify a web server")
        exit(1)

    host = sys.argv[1]
    
    try:
        check_http2(host)
    except:
        print('http2 not supported')
    
    client = smart_web_client(host)

    response = client.send_request()
    
    parse_and_format(response, host)

    client.disconnect()


if __name__=='__main__':
    main()
