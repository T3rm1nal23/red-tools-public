#!/usr/bin/env python3

import http.server as SimpleHTTPServer
import socketserver as SocketServer
import json
import logging
from urllib.parse import urlparse, parse_qs, urlencode
import argparse
import sys
import os
parser = argparse.ArgumentParser()


parser.add_argument("-P", "--port", help="Port to listen on.", type=int, required=True)
parser.add_argument("-I", "--IGNORED_IPS", help="IP Addresses to 'ignore'. Meaning their GET requests will not output logs. Comma separated.")
parser.add_argument("-p", "--reqparam", help="The URI parameter that is required for the server to serve files. Otherwise will give a 503. If applied, reqval must also be applied")
parser.add_argument("-v", "--reqval", help="The URI parameter value that is required for the server to serve files. Otherwise will give a 503. If applied, reqparam must also be applied")
parser.add_argument("-l", "--ALLOW-DIRLIST", help="Allow root directory listing (recommend using reqparam and reqval to stop bots)", action='store_true')
args=parser.parse_args()

PORT = args.port

# Set up logging to both file and console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler("../server.log"),
        logging.StreamHandler()
    ]
)
if args.reqparam or args.reqval:
    if args.reqparam and args.reqval:
        global reqparam
        global reqval
        reqparam = args.reqparam
        reqval = args.reqval
        validate=True
        logging.info("[+] Parameter Validation On")
        logging.info("[+] Required Parameter: ?" + reqparam + "=" + reqval)
    else:
        logging.info("reqval and reqparam must both be set to be used.")
        sys.exit()
else:
    validate=False

if args.IGNORED_IPS:
    IGNORED_IPS = args.IGNORED_IPS.split(',')
else:
    IGNORED_IPS = []

def get_client_ip(self):
    """Retrieve the real client IP from the X-Forwarded-For header (if available)."""
    try:
        forwarded_for = self.headers.get("X-Forwarded-For")
    except:
        forwarded_for = False
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()  # Get the first IP in the list
    return self.client_address[0]  # Fallback to direct client IP

class CORSRequestHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):

    if validate == True:
        reqparam = args.reqparam
        reqval = args.reqval

    def version_string(self):
        return 'nginx'  # Empty string removes the header completely

    if not args.ALLOW_DIRLIST:
        def list_directory(self, path):
            # Respond with a 403 Forbidden instead of listing directories
            #logging.info("[-] Directory listing attempt detected. Request headers:")
            
            logging.info(f"\n[-] Directory listing attempt detected. Request headers:\n-----------------------------\n\nGET {self.path} {self.request_version}\n" + str(self.headers)+"\n-----------------------------\n\n")
            self.send_response(503, "Service Unavailable")
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"<h1>503 Service Unavailable</h1>")
            return True
    
    def log_message(self, format, *args):
        client_ip = get_client_ip(self)
        logging.info("%s - - [%s] %s" % (client_ip,
                                self.log_date_time_string(),
                                format % args))
    
    def deny_request(self):
        self.send_response(503, "Service Unavailable")
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(b"<h1>503 Service Unavailable</h1>")

    def validate_request(self):

        parsed_path = urlparse(self.path)
        params = parse_qs(parsed_path.query)

        # Check if required parameter and value are present
        param_values = params.get(self.reqparam, [])

        if len(param_values) == 0 or param_values[0] != self.reqval:
            logging.info("[-] Parameter Values Don't Match: ?" + reqparam + "=" + reqval)
            #for header, value in self.headers.items():
            #    logging.info(f"{header}: {value}")
            logging.info(f"\n-----------------------------\n\nGET {self.path} {self.request_version}\n" + str(self.headers)+"\n-----------------------------\n\n")
            #logging.info(f"GET {self.path} {self.request_version}")
            #logging.info(self.headers)
            return None
        """
        if (self.reqparam not in params or 
            self.reqval != params[self.reqparam]):
            return False
        """

        # Remove only the required auth parameter from query
        params.pop(self.reqparam)

        # Reconstruct query string with remaining params
        new_query = urlencode(params, doseq=True)
        self.path = parsed_path._replace(query=new_query).geturl()
        return True
    
    def do_OPTIONS(self):
        """Handle preflight requests for CORS"""
        if validate == True:
            if not self.validate_request():
                self.deny_request()
                return
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")  # Allow any origin
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Credentials", "true")
        self.end_headers()
        logging.info(f"\n-----------------------------\n\nOPTIONS {self.path} {self.request_version}\n" + str(self.headers)+"\n-----------------------------\n\n")
        #logging.info(self.headers)

    def do_GET(self):
        """Handle GET requests"""
        #self.send_response(200)
        #self.send_header("Access-Control-Allow-Origin", "*")
        #self.send_header("Content-Type", "application/json")
        #self.end_headers()
        #self.wfile.write(json.dumps({"message": "GET request received"}).encode())
        

        if validate == True:
            if not self.validate_request():
                self.deny_request()
                return
            
        requested_path = self.translate_path(self.path)
        
        if os.path.isdir(requested_path) and not args.ALLOW_DIRLIST:
            # Handle directory listing explicitly and return immediately
            self.list_directory(requested_path)
            return

        client_ip = get_client_ip(self)
        if client_ip not in IGNORED_IPS:
            SimpleHTTPServer.SimpleHTTPRequestHandler.do_GET(self)
            #logging.info("-----------------------------\n\n")
            logging.info(f"\n-----------------------------\n\nGET {self.path} {self.request_version}\n" + str(self.headers)+"\n-----------------------------\n\n")
            #logging.info(self.headers)
        

    def do_POST(self):
        """Handle POST request, log incoming data, and respond with JSON"""

        if validate == True:
            if not self.validate_request():
                self.deny_request()
                return
        
        content_length = int(self.headers.get("Content-Length", 0))  # Get content length
        post_data = self.rfile.read(content_length).decode("utf-8")  # Read and decode data
        logging.info(f"\n-----------------------------\n\nPOST {self.path} {self.request_version}\n" + str(self.headers) + f"-----------------------------\n\nReceived POST data: \n{post_data}\n\n-----------------------------\n\n")
        #logging.info(f"POST {self.path} {self.request_version}")
        #logging.info(self.headers)

        # Log received POST data
        #logging.info(f"-----------------------------\n\nReceived POST data: \n{post_data}\n\n-----------------------------\n\n")  # Logs to 'server.log'

        # Prepare JSON response
        response_data = {"status": "Success", "message": "Data received", "good": "one"}

        # Send HTTP response headers
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Credentials", "true")  # Enable CORS
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Type", "application/json")
        self.end_headers()

        # Send JSON response
        self.wfile.write(json.dumps(response_data).encode("utf-8"))

# Run the server

if __name__ == "__main__":
    SocketServer.TCPServer.allow_reuse_address = True
    with SocketServer.TCPServer(("", PORT), CORSRequestHandler) as httpd:
        logging.info(f"Serving on port {PORT}")
        httpd.serve_forever()
