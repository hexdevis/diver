# Entry point: imports CLI and runs it

import asyncio
import subprocess
import time
from cli import main

def start_ollama_server():
    print("🚀 Starting Ollama Server...")
    process = subprocess.Popen(
        ["ollama", "serve", "qwen3:8b"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    time.sleep(5)  # Give Ollama a few seconds to boot
    return process

if __name__ == "__main__":
        server_process = start_ollama_server()
        try:
          asyncio.run(main())
        except KeyboardInterrupt:
          print("\nExiting...")
        finally:
          server_process.terminate()
          print("🛑 Shutting down Ollama Server...")

