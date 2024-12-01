import socket
import os
import datetime
import mimetypes
from email.utils import parsedate_to_datetime
import threading
import logging
import time

# Configuration
HOST, PORT = '', 8080
BUFFER_SIZE = 4096

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def format_http_date(timestamp):
    """Formats a timestamp into an HTTP-date string."""
    return datetime.datetime.fromtimestamp(timestamp, tz=datetime.timezone.utc).strftime('%a, %d %b %Y %H:%M:%S GMT')

def handle_client(client_connection, client_address):
    try:
        logging.info(f"Connection established with {client_address}")
        while True:
            request = client_connection.recv(BUFFER_SIZE).decode()
            if not request:
                logging.info(f"Connection closed by {client_address}")
                break
            logging.info(f"Received request from {client_address}:\n{request}")

            # Split request into lines
            request_lines = request.split('\r\n')
            request_line = request_lines[0]

            # Parse the request line
            parts = request_line.split()
            if len(parts) != 3:
                # Malformed request line
                logging.error(f"Malformed request line from {client_address}: {request_line}")
                header = 'HTTP/1.1 400 Bad Request\r\nContent-Type: text/html\r\nConnection: close\r\n\r\n'
                error_message = "<h1>400 Bad Request</h1>"
                client_connection.sendall(header.encode() + error_message.encode())
                break  # Close connection after bad request

            method, path, version = parts

            # Only support HTTP/1.1 or HTTP/1.0
            if version not in ['HTTP/1.1', 'HTTP/1.0']:
                logging.error(f"Unsupported HTTP version from {client_address}: {version}")
                header = 'HTTP/1.1 400 Bad Request\r\nContent-Type: text/html\r\nConnection: close\r\n\r\n'
                error_message = "<h1>400 Bad Request</h1>"
                client_connection.sendall(header.encode() + error_message.encode())
                break  # Close connection after bad request

            # Only support GET method
            if method.upper() != 'GET':
                logging.warning(f"Unsupported method from {client_address}: {method}")
                header = 'HTTP/1.1 501 Not Implemented\r\nContent-Type: text/html\r\nConnection: close\r\n\r\n'
                error_message = f"<h1>501 Not Implemented</h1><p>The method {method} is not supported.</p>"
                client_connection.sendall(header.encode() + error_message.encode())
                break  # Close connection after unsupported method

            # Handle the root ("/") request as an index file
            if path == "/":
                path = "/index.html"

            # Remove the leading slash ("/") from the filename
            filepath = path.lstrip('/')

            # Prevent directory traversal attacks
            if '..' in filepath or filepath.startswith('/'):
                logging.error(f"Directory traversal attempt from {client_address}: {filepath}")
                header = 'HTTP/1.1 400 Bad Request\r\nContent-Type: text/html\r\nConnection: close\r\n\r\n'
                error_message = "<h1>400 Bad Request</h1>"
                client_connection.sendall(header.encode() + error_message.encode())
                break  # Close connection after bad request

            # Check if the file exists
            if not os.path.exists(filepath):
                logging.warning(f"File not found for {client_address}: {filepath}")
                header = 'HTTP/1.1 404 Not Found\r\nContent-Type: text/html\r\nConnection: close\r\n\r\n'
                error_message = "<h1>404 Not Found</h1>"
                client_connection.sendall(header.encode() + error_message.encode())
                logging.info(f"File not found: {filepath}")
                break  # Close connection after not found

            # Get file's last modification time
            file_mtime = os.path.getmtime(filepath)
            file_last_modified = format_http_date(file_mtime)
            logging.info(f"File last modified: {file_last_modified}")

            # Parse headers to check for If-Modified-Since
            headers = {}
            for line in request_lines[1:]:
                if line == '':
                    break
                if ':' in line:
                    header_key, header_value = line.split(":", 1)
                    headers[header_key.strip().lower()] = header_value.strip()

            # Determine if the client wants to keep the connection alive
            connection_header = headers.get('connection', '').lower()
            keep_alive = False
            if version == 'HTTP/1.1':
                # HTTP/1.1 defaults to keep-alive unless specified otherwise
                keep_alive = connection_header != 'close'
            elif version == 'HTTP/1.0':
                # HTTP/1.0 defaults to close unless keep-alive is specified
                keep_alive = connection_header == 'keep-alive'

            # Check for If-Modified-Since header
            if 'if-modified-since' in headers:
                try:
                    ims = parsedate_to_datetime(headers['if-modified-since'])
                    if ims.tzinfo is None:
                        ims = ims.replace(tzinfo=datetime.timezone.utc)
                    else:
                        ims = ims.astimezone(datetime.timezone.utc)
                    logging.info(f"If-Modified-Since: {ims}")

                    # Convert file_mtime to datetime
                    file_time = datetime.datetime.fromtimestamp(file_mtime, tz=datetime.timezone.utc)
                    logging.info(f"File time: {file_time}")

                    # Compare times
                    if file_time <= ims:
                        logging.info(f"Not modified since {ims}. Sending 304 Not Modified.")
                        header = 'HTTP/1.1 304 Not Modified\r\n'
                        header += f'Last-Modified: {file_last_modified}\r\n'
                        header += f'Connection: {"keep-alive" if keep_alive else "close"}\r\n'
                        header += '\r\n'
                        client_connection.sendall(header.encode())
                        if not keep_alive:
                            break  # Close connection if not keep-alive
                        else:
                            continue  # Wait for next request
                    else:
                        logging.info(f"Modified since {ims}. Sending 200 OK.")
                except (TypeError, ValueError, OverflowError) as e:
                    logging.error(f"Error parsing If-Modified-Since header: {e}")
                    # If the header is malformed, ignore it and proceed

            # Read and send the file content in chunks (frames)
            try:
                with open(filepath, 'rb') as f:
                    content = f.read()

                # Determine Content-Type based on file extension using mimetypes
                content_type, _ = mimetypes.guess_type(filepath)
                if content_type is None:
                    content_type = 'application/octet-stream'

                # HTTP response headers with chunked transfer encoding
                header = 'HTTP/1.1 200 OK\r\n'
                header += f'Content-Type: {content_type}\r\n'
                header += 'Transfer-Encoding: chunked\r\n'
                header += f'Last-Modified: {file_last_modified}\r\n'
                header += f'Connection: {"keep-alive" if keep_alive else "close"}\r\n'
                header += '\r\n'

                client_connection.sendall(header.encode())

                # Send the content in chunks (frames)
                chunk_size = 4096  # 4KB chunks
                for i in range(0, len(content), chunk_size):
                    chunk = content[i:i+chunk_size]
                    # Send the size of the chunk in hex followed by CRLF
                    client_connection.sendall(f"{len(chunk):X}\r\n".encode())
                    # Send the chunk data followed by CRLF
                    client_connection.sendall(chunk + b"\r\n")
                    time.sleep(0.01)  # Simulate delay for interleaving

                # Send the terminating chunk
                client_connection.sendall(b"0\r\n\r\n")
                logging.info(f"Sent 200 OK response to {client_address}")
            except IOError as e:
                logging.error(f"Error reading file {filepath}: {e}")
                header = 'HTTP/1.1 500 Internal Server Error\r\nContent-Type: text/html\r\nConnection: close\r\n\r\n'
                error_message = "<h1>500 Internal Server Error</h1>"
                client_connection.sendall(header.encode() + error_message.encode())
                break  # Close connection after server error

            # If not keeping the connection alive, close it
            if not keep_alive:
                logging.info(f"Closing connection with {client_address} as per Connection header.")
                break  # Exit the loop to close the connection

    except Exception as e:
        # Handle unexpected exceptions
        logging.error(f"Unexpected error with {client_address}: {e}")
        try:
            header = 'HTTP/1.1 500 Internal Server Error\r\nContent-Type: text/html\r\nConnection: close\r\n\r\n'
            error_message = "<h1>500 Internal Server Error</h1>"
            client_connection.sendall(header.encode() + error_message.encode())
        except:
            pass  # Ignore errors while sending error response
        finally:
            logging.info(f"Closing connection with {client_address} due to an error.")

    finally:
        client_connection.close()
        logging.info(f"Closed connection with {client_address}")

def start_server():
    # Create a listening socket
    listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listen_socket.bind((HOST, PORT))
    listen_socket.listen(100)  # Increased backlog for handling more connections
    logging.info(f'Serving HTTP on port {PORT} ...')

    while True:
        try:
            # Accept client connections
            client_connection, client_address = listen_socket.accept()
            logging.info(f"Accepted connection from {client_address}")

            # Handle each client connection in a new thread
            client_thread = threading.Thread(target=handle_client, args=(client_connection, client_address))
            client_thread.daemon = True  # Daemonize thread to exit when main thread does
            client_thread.start()

        except KeyboardInterrupt:
            logging.info("Shutting down the server.")
            listen_socket.close()
            break
        except Exception as e:
            logging.error(f"Error accepting connections: {e}")
            listen_socket.close()
            break

if __name__ == "__main__":
    start_server()
