# File I/O helpers (get_code_files, read_file, write_file, chunk_text)
import os, glob

# ANSI color codes
def _ansi(code: str) -> str:
    return f"\x1B[{code}m"

def color(text: str, code: str) -> str:
    return f"{_ansi(code)}{text}{_ansi('0')}"

def green(text: str) -> str:
    return color(text, '32')

def yellow(text: str) -> str:
    return color(text, '33')

def cyan(text: str) -> str:
    return color(text, '36')

def magenta(text: str) -> str:
    return color(text, '35')

def grey(text: str) -> str:
    return color(text, '37')

def blue(text: str) -> str:
    return color(text, '34')


def get_code_files(path, exts=(".py", ".js", ".cpp", ".java", ".ts")):
    files = []
    for ext in exts:
        files.extend(glob.glob(os.path.join(path, f"**/*{ext}"), recursive=True))
    return files

def read_file(fp):
    try:
        with open(fp, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""

def write_file(fp, content):
    with open(fp, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Updated {fp}")

def chunk_text(text, size=512):
    lines = text.splitlines()
    for i in range(0, len(lines), size):
        yield "\n".join(lines[i:i+size])
