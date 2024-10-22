# cmpt-371-mp1

## Instructions to Run Step 1 and 2

1. Clone the repository to your local machine:
   ```bash 
   git clone https://github.com/yourusername/repository-name.git
    ```

2. **Open the terminal and go to directory

3. Run Python server:
    ```bash 
   python3 server.py
    ```
    OR
    ```bash 
   python server.py
    ```

4. Open a new terminal window, same directory, and run:
    ```bash 
   curl -v http://127.0.0.1:8080/test.html
    ```

5. Make sure you see something like the following in the new terminal:
    ```bash
   *   Trying 127.0.0.1:8080...
   * Connected to 127.0.0.1 (127.0.0.1) port 8080
   > GET /test.html HTTP/1.1
   > Host: 127.0.0.1:8080
   > User-Agent: curl/8.7.1
   > Accept: */*
   > 
   * Request completely sent off
   < HTTP/1.1 200 OK
   < Content-Type: text/html
   < 
   * no chunk, no close, no size. Assume close to signal end
   <!DOCTYPE html>
   <html>

   <head>
     <meta charset="utf-8">
     <title></title>
     <meta name="author" content="">
     <meta name="description" content="">
     <meta name="viewport" content="width=device-width, initial-scale=1">

   </head>

   <body>

     <p>Congratulations! Your Web Server is Working!</p>

   </body>

   </html>
   * Closing connection
   ```