#!/usr/bin/env python3

#python3 ./redirector.py 8000 http://127.0.0.1/
#AWS MD redirect python redirector.py 8000 http://169.254.169.254/latest/user-data
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler

if len(sys.argv)-1 != 2:
    print("Usage: {} <port_number> <url>".format(sys.argv[0]))
    print ("AWS Redirect Example - 'python redirector.py 8000 http://169.254.169.254/latest/user-data'")
    sys.exit()

class Redirect(BaseHTTPRequestHandler):
   def do_GET(self):
       self.send_response(301)
       self.send_header('Location', sys.argv[2])
       self.end_headers()

HTTPServer(("", int(sys.argv[1])), Redirect).serve_forever()
