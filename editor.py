# Async edit helpers (edit_answer, edit_file)

import os
from utils import read_file, write_file
from prompt_toolkit import PromptSession

async def edit_answer(session: PromptSession, answer: str, matches):
    print("\n--- Model Suggestion ---\n")
    print(answer)
    print("\n--- End Suggestion ---\n")

    edit = await session.prompt_async("Edit before applying? (y/n) ")
    if edit.lower() == "y":
        new_code = await session.prompt_async("Edit:\n", multiline=True)
        answer = new_code

    for src, _ in matches:
        write_file(src, answer)

async def edit_file(session: PromptSession, filename: str):
    if not os.path.isfile(filename):
        print(f"File not found: {filename}")
        return
    content = read_file(filename)
    print(f"\n--- Editing {filename} ---\n")
    print(content)
    new_content = await session.prompt_async("Edit:\n", multiline=True)
    write_file(filename, new_content)

