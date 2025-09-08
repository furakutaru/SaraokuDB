import os
import sys
import subprocess
import time
import signal
import requests
from typing import Optional

def start_server():
    """Start the FastAPI server in a subprocess"""
    # Kill any existing processes using port 8000
    try:
        subprocess.run(['pkill', '-f', 'uvicorn backend.main:app'], 
                      stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except:
        pass
    
    # Start the server with the correct Python path
    env = os.environ.copy()
    env['PYTHONPATH'] = os.path.dirname(os.path.abspath(__file__))
    
    # Start the server in a subprocess
    server_process = subprocess.Popen(
        [sys.executable, '-m', 'uvicorn', 'backend.main:app', '--reload', '--host', '0.0.0.0', '--port', '8000'],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Wait for the server to start
    time.sleep(5)
    
    return server_process

def test_api_endpoints():
    """Test the API endpoints"""
    base_url = "http://localhost:8000"
    
    # Test the root endpoint
    try:
        print("\n=== Testing root endpoint ===")
        response = requests.get(f"{base_url}/")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error testing root endpoint: {e}")
    
    # Test the horses endpoint
    try:
        print("\n=== Testing horses endpoint ===")
        response = requests.get(f"{base_url}/horses/")
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Number of horses: {len(data) if isinstance(data, list) else 'N/A'}")
        if data and len(data) > 0:
            print(f"First horse: {data[0].get('name')} (ID: {data[0].get('id')})")
    except Exception as e:
        print(f"Error testing horses endpoint: {e}")
    
    # Test the statistics endpoint
    try:
        print("\n=== Testing statistics endpoint ===")
        response = requests.get(f"{base_url}/statistics/")
        print(f"Status: {response.status_code}")
        print(f"Statistics: {response.json()}")
    except Exception as e:
        print(f"Error testing statistics endpoint: {e}")

def main():
    print("Starting FastAPI server...")
    server_process = start_server()
    
    try:
        # Test the API endpoints
        test_api_endpoints()
        
        # Keep the server running until interrupted
        print("\nServer is running. Press Ctrl+C to stop.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping server...")
        server_process.terminate()
        server_process.wait()
        print("Server stopped.")
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        server_process.terminate()
        server_process.wait()
        sys.exit(1)

if __name__ == "__main__":
    main()
