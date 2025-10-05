# Interactive CLI, commands

import asyncio
from prompt_toolkit import PromptSession
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.application import run_in_terminal
from indexer import index_codebase
from config import get_collection
from search import search_code
from editor import edit_answer, edit_file
from model import ask_model

async def main():
    # Lazily get the collection to avoid heavy imports at module import time.
    collection = get_collection()
    if collection.count() == 0:
        index_codebase()

    session = PromptSession()
    bindings = KeyBindings()

    @bindings.add("c-c")
    def _(event):
        event.app.exit()
        print("\nExiting...")

    print("\n🐬 Diver CLI")
    print("Commands: :index | :search query | :edit file | :quit\n")

    while True:
        q = await session.prompt_async("\n> ", key_bindings=bindings)

        if q.startswith(":"):
            cmd_parts = q[1:].split(maxsplit=1)
            cmd = cmd_parts[0]

            if cmd in ["quit", "exit"]:
                print("Exiting...")
                break

            elif cmd == "index":
                index_codebase()

            elif cmd == "search" and len(cmd_parts) > 1:
                query = cmd_parts[1]
                matches = search_code(query)
                for src, chunk in matches:
                    print(f"\nFile: {src}\n{chunk}\n{'-'*40}")

            elif cmd == "edit" and len(cmd_parts) > 1:
                filename = cmd_parts[1]
                await edit_file(session, filename)

            else:
                print(f"Unknown command: {cmd}")

        else:
            matches = search_code(q)
            context = "\n\n".join([f"File: {src}\n{chunk}" for src, chunk in matches])
            answer = await asyncio.to_thread(ask_model, q, context)
            print("\n🤖 Thinking...\n")
            await edit_answer(session, answer, matches)

