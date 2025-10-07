import asyncio
import subprocess
import signal
import sys
import os
from cli import main


def start_ollama_server():
  print("Starting Server...")
  process = subprocess.Popen(
    ["ollama", "serve", "qwen3:8b"],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
  )
  return process


def _cleanup_and_exit(server_process, code=0):
  try:
    print("\nExiting...", flush=True)
    sys.stdout.flush()
  except Exception:
    pass
  if server_process is not None:
    try:
      server_process.terminate()
    except Exception:
      pass
    try:
      print("Shutting Server...", flush=True)
      sys.stdout.flush()
    except Exception:
      pass
  try:
    os._exit(code)
  except Exception:
    try:
      sys.exit(code)
    except SystemExit:
      raise


if __name__ == "__main__":
  server_process = None
  # start server first so signals during startup are also handled
  try:
    server_process = start_ollama_server()

    # capture signal handlers to ensure clean shutdown
    def _handler(signum, frame):
      # call cleanup and force exit
      _cleanup_and_exit(server_process, 0)

    signal.signal(signal.SIGINT, _handler)
    signal.signal(signal.SIGTERM, _handler)

    try:
      asyncio.run(main())
    except (KeyboardInterrupt, EOFError):
      _cleanup_and_exit(server_process, 0)
  except Exception:
    # cleanup on unexpected errors
    if server_process is not None:
      try:
        server_process.terminate()
      except Exception:
        pass
    raise
