import subprocess
import json
import time
from utils import cyan, green

def ask_model(query: str, context: str, model: str = "qwen3:8b") -> str:
    """
    Send a structured prompt to a local Ollama model (default: qwen3:8b).

    Args:
        query (str): The user's question or request.
        context (str): Relevant project or code context to help model reasoning.
        model (str): The Ollama model tag to use (e.g. 'llama3', 'mistral', etc.)

    Returns:
        str: The model's response text or an error message.
    """

    # --- Construct system + user prompt ---
    prompt = f"""
You are a coding assistant with access to project context.

User question:
{query}

Relevant code context:
{context}

Answer concisely and clearly.
"""

    start_time = time.time()

    # Print a colored 'thinking' status
    print(cyan("\n🧠 Thinking..."))

    try:
        # --- Spawn the subprocess for Ollama inference ---
        # This runs locally: `ollama run <model>`
        process = subprocess.Popen(
            ["ollama", "run", model],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # --- Send prompt to model and wait for output ---
        stdout, stderr = process.communicate(input=prompt, timeout=180)

        elapsed = round(time.time() - start_time, 2)
        print(green(f"✅ Inference completed in {elapsed}s"))
        print("🧩", stdout)

        # --- Error handling ---
        if process.returncode != 0:
            print("⚠️ Model process exited with error code:", process.returncode)
            if stderr:
                print("🪶 STDERR (excerpt):", stderr[:200])
            return f"❌ Model process failed (code {process.returncode})."

        if not stdout.strip():
            return "⚠️ Model returned no output."

        # --- Optionally: Try to parse structured JSON output ---
        # If your model returns structured data, you can parse it here.
        try:
            return json.loads(stdout)
        except json.JSONDecodeError:
            # Not JSON — just return plain text
            return stdout.strip()

    except subprocess.TimeoutExpired:
        return "⏳ Model timed out after 180 seconds."
    except FileNotFoundError:
        return "❌ Ollama not found. Make sure it's installed and running (`ollama serve`)."
    except Exception as e:
        return f"❌ Unexpected error during inference: {e}"


