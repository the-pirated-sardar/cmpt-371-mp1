import socket
import os
import datetime
import time
from email.utils import parsedate_to_datetime

HOST, PORT = '', 8080

listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
listen_socket.bind((HOST, PORT))
listen_socket.listen(1)
print(f'Serving HTTP on port {PORT} ...')

def format_http_date(timestamp):
    return datetime.datetime.fromtimestamp(timestamp, datetime.UTC)

while True:
    try:
        client_connection, client_address = listen_socket.accept()
        request = client_connection.recv(1024).decode()
        print(request)

        if not request:
            client_connection.close()
            continue

        # Split request into lines
        request_lines = request.split('\r\n')
        request_line = request_lines[0]

        # Parse the request line
        parts = request_line.split()
        if len(parts) != 3:
            # Malformed request line
            header = 'HTTP/1.1 400 Bad Request\r\n\r\n'
            error_message = "<h1>400 Bad Request</h1>"
            client_connection.sendall(header.encode())
            client_connection.sendall(error_message.encode())
            client_connection.close()
            continue

        method, path, version = parts

        # Only support HTTP/1.1 or HTTP/1.0
        if version not in ['HTTP/1.1', 'HTTP/1.0']:
            header = 'HTTP/1.1 400 Bad Request\r\n\r\n'
            error_message = "<h1>400 Bad Request</h1>"
            client_connection.sendall(header.encode())
            client_connection.sendall(error_message.encode())
            client_connection.close()
            continue

        # Only support GET method
        if method != 'GET':
            header = 'HTTP/1.1 501 Not Implemented\r\n\r\n'
            error_message = f"<h1>501 Not Implemented</h1><p>The method {method} is not supported.</p>"
            client_connection.sendall(header.encode())
            client_connection.sendall(error_message.encode())
            client_connection.close()
            continue

        # Handle the root ("/") request as an index file
        if path == "/":
            path = "/index.html"

        # Remove the leading slash ("/") from the filename
        filepath = path.lstrip('/')

        # Prevent directory traversal attacks
        if '..' in filepath or filepath.startswith('/'):
            header = 'HTTP/1.1 400 Bad Request\r\n\r\n'
            error_message = "<h1>400 Bad Request</h1>"
            client_connection.sendall(header.encode())
            client_connection.sendall(error_message.encode())
            client_connection.close()
            continue

        # Check if the file exists
        if not os.path.exists(filepath):
            # Handle file not found (404 error)
            header = 'HTTP/1.1 404 Not Found\r\nContent-Type: text/html\r\n\r\n'
            error_message = "<h1>404 Not Found</h1>"
            client_connection.sendall(header.encode())
            client_connection.sendall(error_message.encode())
            client_connection.close()
            continue

        # Get file's last modification time
        file_mtime = os.path.getmtime(filepath)
        file_last_modified = format_http_date(file_mtime)
        print(f"File last modified: {file_last_modified}")

        # Parse headers to check for If-Modified-Since
        headers = {}
        for line in request_lines[1:]:
            if line == '':
                break
            header_key, header_value = line.split(":", 1) if ":" in line else (None, None)
            if header_key and header_value:
                headers[header_key.strip().lower()] = header_value.strip()

        # Check for If-Modified-Since header
        if 'if-modified-since' in headers:
            try:
                ims = parsedate_to_datetime(headers['if-modified-since'])
                if ims.tzinfo is None:
                    ims = ims.replace(tzinfo=datetime.timezone.utc)
                else:
                    ims = ims.astimezone(datetime.timezone.utc)
                print(f"If-Modified-Since: {ims}")
                # Convert file_mtime to datetime
                file_time = datetime.datetime.fromtimestamp(file_mtime,tz=datetime.timezone.utc)
                print(f"File time: {file_time}")
                # Compare times
                if file_time <= ims:
                    print("Not modified")
                else:
                    print("Modified")
                if file_time <= ims:
                    # Not modified
                    header = 'HTTP/1.1 304 Not Modified\r\n'
                    header += f'Last-Modified: {file_last_modified}\r\n'
                    header += '\r\n'
                    client_connection.sendall(header.encode())
                    client_connection.close()
                    continue
            except (TypeError, ValueError, OverflowError):
                # If the header is malformed, ignore it and proceed
                pass

        # Read and send the file content
        with open(filepath, 'rb') as f:
            content = f.read()

        # Determine Content-Type based on file extension (basic implementation)
        if filepath.endswith('.html'):
            content_type = 'text/html'
        

        # HTTP response headers
        header = 'HTTP/1.1 200 OK\r\n'
        header += f'Content-Type: {content_type}\r\n'
        header += f'Content-Length: {len(content)}\r\n'
        header += f'Last-Modified: {file_last_modified}\r\n'
        header += 'Connection: close\r\n'
        header += '\r\n'

        client_connection.sendall(header.encode())
        client_connection.sendall(content)
        client_connection.close()

    except Exception as e:
        # Handle unexpected exceptions
        print(f"Error: {e}")
        try:
            header = 'HTTP/1.1 500 Internal Server Error\r\n\r\n'
            error_message = "<h1>500 Internal Server Error</h1>"
            client_connection.sendall(header.encode())
            client_connection.sendall(error_message.encode())
        except:
            pass
        finally:
            client_connection.close()
