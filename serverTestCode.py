import subprocess

def run_curl_command(command, description):
    print(f"\n=== {description} ===")
    try:
        result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        if result.stdout:
            print("Standard Output:")
            print(result.stdout)
        if result.stderr:
            print("Standard Error:")
            print(result.stderr)
    except subprocess.CalledProcessError as e:
        # Handle errors in command execution
        print(f"Error executing command: {e.stderr}")

def main():
    # Test 200 OK - Normal request for an existing file
    cmd_200 = 'curl -v http://127.0.0.1:8080/test.html'
    run_curl_command(cmd_200, "Test 200 OK")
    
    # Test 304 Not Modified - Conditional GET with If-Modified-Since header
    cmd_304 = 'curl -v -H "If-Modified-Since: Wed, 23 Oct 2024 07:28:00 GMT" http://127.0.0.1:8080/test.html'
    run_curl_command(cmd_304, "Test 304 Not Modified")
    
    # Test 400 Bad Request - Malformed request for a file with invalid characters
    cmd_400 = 'curl -v http://127.0.0.1:8080/test..html'
    run_curl_command(cmd_400, "Test 400 Bad Request")
    
    # Test 404 Not Found - Request for a file that does not exist
    cmd_404 = 'curl -v http://127.0.0.1:8080/testNotExist.html'
    run_curl_command(cmd_404, "Test 404 Not Found")
    
    # Test 501 Not Implemented - POST request (unsupported by the server)
    cmd_501 = 'curl -X POST -v http://127.0.0.1:8080/test.html'
    run_curl_command(cmd_501, "Test 501 Not Implemented")

if __name__ == "__main__":
    main()
