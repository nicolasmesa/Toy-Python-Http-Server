import socket
import threading
from pathlib import Path
import datetime


class Request():
	def __init__(self, request_lines):
		self.request_lines = request_lines
		self.method, self.path, self.protocol  = request_lines[0].upper().split()
		self.populate_headers(request_lines[1:])
		
	def populate_headers(self, headers):
		self.headers = {}
		for header in headers:
			split = header.split(':')
			if len(split) == 1:
				self.headers[header.lower()] = ''
				continue

			key = split[0].lower()
			value = ':'.join(split[1:])
			self.headers[key] = value


class Response():
	def __init__(self):
		self.payload = ''
		self.content_length = 0
		self.headers = {}
		self.code = 200
		self.message = 'OK' 
	
	def add_header(self, key, value):
		self.headers[key] = value

	def set_payload(self, payload):
		if type(payload) is not bytes:
			payload = str(payload)
			payload = payload.encode('utf-8')
				
		self.payload = payload
		self.content_length = len(payload)

	def set_status_code(self, code):
		self.code = code

	def set_status_message(self, message):
		self.message = message

	def send_response(self, connection):
		headers = [
			'HTTP/1.1 ' + str(self.code) + ' ' + self.message
		]

		for key in self.headers:
			headers.append(key + ': ' + self.headers[key])

		headers.append('content-length: ' + str(self.content_length))

		headers_bytes = ('\n'.join(headers) + '\n\n').encode('utf-8')

		connection.write(headers_bytes)
		connection.write(self.payload)
		

def log(message):
	print(datetime.datetime.now().isoformat('T'), message)


def get_line(connection):
	line = b''
	while True:
		c = connection.read(1)
		if c == b'\n' or c == b'\r':
			# skip \r or \n
			connection.read(1)
			return line.decode("utf-8") 
		line += c

def read_request(connection):
	req = []
	while True:
		line = get_line(connection)
		if line == '':
			break
		req.append(line)

	request = Request(req)
	return request


def get_payload(path):
	file_path = Path(path)
	if file_path.is_file():
		with open(path, 'rb') as f:
			return f.read()
	return None
	

def handle_connection(connection):
	request = read_request(connection)

	print(request.request_lines[0])

	path = request.path
	if path == '/':
		path = 'index.html'

	path = 'public/' + path

	response = Response()
	response.add_header('content-type', 'text/html')

	payload = get_payload(path)

	if payload is None:
		response.set_payload('<h1>Not found</h1>')
		response.set_status_code(404)
		response.set_status_message("Not Found")
	else:
		response.set_payload(payload)

	response.send_response(connection)
	connection.close()

	log('"{}" {} {}'.format(request.request_lines[0] , response.code, response.content_length))



if __name__ == "__main__":
	server_socket = socket.socket()
	server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	server_socket.bind(('', 8080))
	server_socket.listen(0)

	while True:
		print("Waiting for connection")
		connection = server_socket.accept()[0].makefile('rwb')
		print("Connection accepted")
		handle_connection(connection)
