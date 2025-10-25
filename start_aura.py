#!/usr/bin/env python3
"""
A.U.R.A Simple Launcher
Starts the web interface and NewAI API
"""

import http.server
import socketserver
import subprocess
import sys
import threading
import time
import os
from pathlib import Path

def start_web_interface():
    """Start the web interface server"""
    try:
        print("🌐 Starting Web Interface...")
        PORT = 8080
        DIRECTORY = "."
        
        class Handler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=DIRECTORY, **kwargs)
        
        os.chdir(DIRECTORY)
        with socketserver.TCPServer(("", PORT), Handler) as httpd:
            print(f"✅ Web Interface: http://localhost:{PORT}")
            httpd.serve_forever()
    except Exception as e:
        print(f"❌ Error starting web interface: {e}")

def start_newai_api():
    """Start the NewAI API server"""
    try:
        print("🧠 Starting NewAI API...")
        subprocess.run([sys.executable, "newai_api.py"], check=True)
    except Exception as e:
        print(f"❌ Error starting NewAI API: {e}")

def main():
    """Main launcher function"""
    print("🤖 A.U.R.A - Adaptive User Retention Assistant")
    print("=" * 60)
    print("🚀 Starting A.U.R.A Services...")
    print("")
    
    # Start services in background threads
    web_thread = threading.Thread(target=start_web_interface, daemon=True)
    api_thread = threading.Thread(target=start_newai_api, daemon=True)
    
    web_thread.start()
    time.sleep(2)  # Give web interface time to start
    api_thread.start()
    
    print("")
    print("✅ A.U.R.A Services Started!")
    print("=" * 60)
    print("🌐 Web Interface: http://localhost:8080")
    print("🧠 NewAI API: http://localhost:8081")
    print("")
    print("📊 Features Available:")
    print("   • Interactive Dashboard with Tabs")
    print("   • NewAI Churn Prediction Model")
    print("   • AI Chatbot Assistant")
    print("   • CSV Upload and Processing")
    print("   • Real predictions.csv Output")
    print("")
    print("🛑 Press Ctrl+C to stop all services")
    print("=" * 60)
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Stopping A.U.R.A services...")
        print("✅ All services stopped")

if __name__ == "__main__":
    main()
