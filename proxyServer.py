import socket
import threading

def handle_client(client_socket):
    # Receive the request from the client
    request = client_socket.recv(4096)
    if not request:
        client_socket.close()
        return

    # Decode the request to extract information
    try:
        request_line = request.decode().split('\n')[0]
        method, url, protocol = request_line.split()
    except ValueError:
        client_socket.close()
        return

    # Only handle absolute URLs (required for proxy)
    if not url.startswith('http://'):
        response = 'HTTP/1.1 400 Bad Request\r\n\r\n'
        client_socket.sendall(response.encode())
        client_socket.close()
        return

    # Extract the hostname and the path
    url = url[7:]  # Remove 'http://'
    host_end = url.find('/')
    if host_end == -1:
        host = url
        path = '/'
    else:
        host = url[:host_end]
        path = url[host_end:]

    # Split host and port if specified
    if ':' in host:
        host, port = host.split(':')
        port = int(port)
    else:
        port = 80

    try:
        # Create a socket to connect to the destination server
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.connect((host, port))

        # Modify the request line to be relative to the server
        new_request_line = f"{method} {path} {protocol}\r\n"
        headers = request.decode().split('\r\n')[1:]
        headers = [header for header in headers if not header.lower().startswith('proxy-connection')]
        new_request = new_request_line + '\r\n'.join(headers)
    

        # Send the modified request to the destination server
        server_socket.sendall(new_request.encode())

        # Receive the response from the server and send it back to the client
        while True:
            data = server_socket.recv(4096)
            if len(data) > 0:
                client_socket.sendall(data)
            else:
                break

        # Close both sockets
        server_socket.close()
        client_socket.close()
    except Exception as e:
        print(f"Error: {e}")
        client_socket.close()

def start_proxy_server(host='127.0.0.1', port=8888):
    proxy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    proxy_socket.bind((host, port))
    proxy_socket.listen(100)
    print(f"Proxy server listening on {host}:{port}")

    while True:
        client_socket, addr = proxy_socket.accept()
        print(f"Received connection from {addr}")
        client_thread = threading.Thread(target=handle_client, args=(client_socket,))
        client_thread.start()

if __name__ == '__main__':
    start_proxy_server()
