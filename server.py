import socket
import os

HOST, PORT = '', 8080

listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
listen_socket.bind((HOST, PORT))
listen_socket.listen(1)
print('Serving HTTP on port %s ...' % PORT)

while True:
    try:
        client_connection, client_address = listen_socket.accept()
        request = client_connection.recv(1024).decode()
        print(request)
        
        if not request:
            continue
        
        # Extract the requested file path from the request
        filename = request.split()[1]  # filename will be /test.html in this case
        
        # Handle the root ("/") request as an index file (optional)
        if filename == "/":
            filename = "/index.html"
        
        # Remove the leading slash ("/") from the filename
        filepath = filename[1:]

        # Check if the file exists before attempting to open it
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding="utf-8") as f:
                outputRequest = f.read()

            # HTTP response headers
            header = 'HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n'
            client_connection.sendall(header.encode())
            client_connection.sendall(outputRequest.encode())  # Send the file content at once
        else:
            # Handle file not found (404 error)
            header = 'HTTP/1.1 404 Not Found\r\n\r\n'
            error_message = "<h1>404 Not Found</h1>"
            client_connection.sendall(header.encode())
            client_connection.sendall(error_message.encode())

        # Close the connection after the response is sent
        client_connection.close()
    
    except IOError:
        # Handle exceptions that may occur during file handling
        header = 'HTTP/1.1 500 Internal Server Error\r\n\r\n'
        client_connection.sendall(header.encode())
        client_connection.close()
