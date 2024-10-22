import subprocess

def run_curl_command(command, description):
    print(f"\n=== {description} ===")
    try:
        result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        if result.stdout:
            print("Standard Output:")
            print(result.stdout)
        elif result.stderr:
            print("Standard Error:")
            print(result.stderr)
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e.stderr}")

def main():
    proxy = 'localhost:8888'
    
    # Test 200 OK
    cmd_200 = f'curl -x {proxy} http://127.0.0.1:8080/test.html -v'
    run_curl_command(cmd_200, "Test 200 OK")
    
    # Test 304 Not Modified
    # Conditional GET        working fine in terminal
    cmd_304 = f'curl.exe -x {proxy} -v -H "If-Modified-Since: Wed, 23 Oct 2024 07:28:00 GMT" http://127.0.0.1:8080/test.html'
    run_curl_command(cmd_304, "Test 304 Not Modified")

    # Test 400 Bad Request
    cmd_400 = f'curl -x {proxy} http://127.0.0.1:8080/test..html -v --raw'
    run_curl_command(cmd_400, "Test 400 Bad Request")
    
    # Test 404 Not Found
    cmd_404 = f'curl -x {proxy} http://127.0.0.1:8080/testNotExist.html -v'
    run_curl_command(cmd_404, "Test 404 Not Found")
    
    # Test 501 Not Implemented
    cmd_501 = f'curl -x {proxy} -X POST http://127.0.0.1:8080/test.html -v'
    run_curl_command(cmd_501, "Test 501 Not Implemented")

if __name__ == "__main__":
    main()
