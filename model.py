# Load embedding model and LLM connection
# Speed note, Run: ollama serve .

import subprocess

def ask_model(query, context):
    prompt = f"""
You are a coding assistant with access to project context.

User question:
{query}

Relevant code context:
{context}

Answer concisely and clearly.
"""

    print("\n🧠 Sending to Ollama...\n")

    try:
        process = subprocess.Popen(
            ["ollama", "run", "qwen3:8b"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Send the prompt and close stdin
        stdout, stderr = process.communicate(input=prompt, timeout=180)  # give 3 minutes

        print("🧩 Ollama STDOUT:\n", stdout[:400])
        print("⚠️ Ollama STDERR:\n", stderr[:200])

        if not stdout.strip():
            return "⚠️ Model returned no output."

        return stdout.strip()

    except subprocess.TimeoutExpired:
        return "⏳ Model timed out"
    except Exception as e:
        return f"❌ Error calling Ollama: {e}"
