import asyncio
from prompt_toolkit import PromptSession
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.application import run_in_terminal
from indexer import index_codebase
from config import get_collection, DEFAULTS
from model import ask_model
from utils import read_file, green, yellow, cyan, magenta

async def main():
    # get the collection to avoid heavy imports at module import time.
    # import search_code to avoid static import resolution issues
    try:
        import importlib

        search_mod = importlib.import_module("search")
        search_code = getattr(search_mod, "search_code")
    except Exception:
        # Fallback: no-op search (returns empty list)
        def search_code(q):
            return []

    collection = get_collection()
    if collection.count() == 0:
        index_codebase()

    session = PromptSession()
    bindings = KeyBindings()

    @bindings.add("c-c")
    def _(event):
        # exit the prompt and re-raise KeyboardInterrupt in main
        event.app.exit(exception=KeyboardInterrupt())

    @bindings.add("c-d")
    def _eof(event):
        event.app.exit(exception=EOFError())

    print("\n🐬 Diver CLI")
    print("Commands: :index | :find query | :edit file | :run file | :quit")

    while True:
        q = await session.prompt_async("> ", key_bindings=bindings)

        if q.startswith(":"):
            cmd_parts = q[1:].split(maxsplit=1)
            cmd = cmd_parts[0]

            if cmd in ["quit", "exit"]:
                print("Exiting...")
                break

            elif cmd == "index":
                index_codebase()

            elif cmd == "cd":
                import os

                target = cmd_parts[1] if len(cmd_parts) > 1 else None
                if not target:
                    target = os.path.expanduser("~")
                try:
                    # expand env. variables
                    path = os.path.expanduser(os.path.expandvars(target))
                    os.chdir(path)
                    print(f"Changed directory to {os.getcwd()}")
                except Exception as e:
                    print(f"cd: {e}")

            elif cmd == "run":
                # run/compile files for multiple languages; if no path provided, prompt for it.
                path = cmd_parts[1] if len(cmd_parts) > 1 else None
                if not path:
                    path = await session.prompt_async("File to run: ")
                    if not path:
                        print("No file specified.")
                        continue

                def _compile_and_run():
                    import os
                    import subprocess
                    import shutil

                    _, ext = os.path.splitext(path)
                    ext = ext.lower()

                    def run_cmd(cmd_args):
                        print("Running:", " ".join(cmd_args))
                        try:
                            subprocess.check_call(cmd_args)
                        except FileNotFoundError:
                            print(f"Command not found: {cmd_args[0]}")
                            return False
                        except subprocess.CalledProcessError as e:
                            print(f"Process exited with code: {e.returncode}")
                            return False
                        return True

                    # compile to a binary and run it
                    def compile_and_run(compiler, args, bin_path):
                        import os
                        build_dir = DEFAULTS.get("build_dir") or "build"
                        os.makedirs(build_dir, exist_ok=True)

                        # ensure binary path is inside build_dir to avoid name collisions
                        base = os.path.basename(bin_path)
                        full_bin_path = os.path.join(build_dir, base)

                        cmd = [compiler] + args
                        # if args contains '-o' followed by filename, replace that
                        if "-o" in cmd:
                            o_idx = cmd.index("-o")
                            if o_idx + 1 < len(cmd):
                                cmd[o_idx + 1] = full_bin_path

                        print("Compiling:", " ".join(cmd))
                        try:
                            subprocess.check_call(cmd)
                        except FileNotFoundError:
                            print(f"Compiler not found: {compiler}")
                            return
                        except subprocess.CalledProcessError as e:
                            print(f"Compilation failed with code: {e.returncode}")
                            return

                        # run the produced binary. Use absolute path in build_dir.
                        run_cmd([full_bin_path])

                    # dispatch by extension
                    if ext == ".py":
                        # py script
                        py_exec = shutil.which(DEFAULTS.get("python")) or shutil.which("python")
                        if not py_exec:
                            print("Python interpreter not found")
                            return
                        run_cmd([py_exec, path])

                    elif ext == ".js":
                        node = shutil.which(DEFAULTS.get("node"))
                        if not node:
                            print("Node.js not found")
                            return
                        run_cmd([node, path])

                    elif ext == ".ts":
                        # prefer npx ts-node, fall back to tsc+node
                        npx = shutil.which(DEFAULTS.get("npx"))
                        ts_node = shutil.which(DEFAULTS.get("ts_node"))
                        if npx:
                            run_cmd([npx, "ts-node", path])
                        elif ts_node:
                            run_cmd([ts_node, path])
                        else:
                            tsc = shutil.which(DEFAULTS.get("tsc"))
                            if not tsc:
                                print("No TypeScript runner found (npx/ts-node/tsc). Install ts-node or use npx.")
                                return
                            # compile to temporary js file
                            out_dir = ".ts_build"
                            os.makedirs(out_dir, exist_ok=True)
                            try:
                                subprocess.check_call([tsc, path, "--outDir", out_dir])
                            except subprocess.CalledProcessError as e:
                                print(f"tsc failed: {e.returncode}")
                                return
                            # find compiled file name
                            base = os.path.splitext(os.path.basename(path))[0] + ".js"
                            compiled = os.path.join(out_dir, base)
                            node = shutil.which("node")
                            if not node:
                                print("Node.js not found to run compiled TypeScript")
                                return
                            run_cmd([node, compiled])

                    elif ext == ".rs":
                        # rustc file -o bin
                        rustc = shutil.which(DEFAULTS.get("rustc"))
                        if not rustc:
                            print("rustc not found; install Rust toolchain")
                            return
                        bin_path = os.path.splitext(path)[0]
                        compile_and_run(rustc, [path, "-o", bin_path], bin_path)

                    elif ext == ".c":
                        gcc = shutil.which(DEFAULTS.get("gcc")) or shutil.which(DEFAULTS.get("clang"))
                        if not gcc:
                            print("C compiler not found (gcc/clang)")
                            return
                        bin_path = os.path.splitext(path)[0]
                        compile_and_run(gcc, [path, "-std=c17", "-O2", "-o", bin_path], bin_path)

                    elif ext in (".cpp", ".cc", ".cxx"):
                        gpp = shutil.which(DEFAULTS.get("gpp")) or shutil.which(DEFAULTS.get("clangpp"))
                        if not gpp:
                            print("C++ compiler not found (g++/clang++)")
                            return
                        bin_path = os.path.splitext(path)[0]
                        compile_and_run(gpp, [path, "-std=c++17", "-O2", "-o", bin_path], bin_path)

                    else:
                        print(f"Unsupported file extension: {ext}")
                        return

                # run the compile/run sequence in the terminal so processes can own stdin/stdout
                run_in_terminal(_compile_and_run)


            elif cmd == "edit":
                # if no path provided, prompt for it.
                path = cmd_parts[1] if len(cmd_parts) > 1 else None
                if not path:
                    path = await session.prompt_async("File to edit: ")
                    if not path:
                        print("No file specified.")
                        continue

                def _open_in_editor():
                    import os
                    import tempfile
                    import subprocess

                    editor = os.environ.get("EDITOR", "vim")

                    # make a temp file with the same suffix as the target
                    suffix = os.path.splitext(path)[1] or None
                    tf = tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=suffix)
                    tmpname = tf.name
                    try:
                        # write current contents if file exists
                        try:
                            with open(path, "r", encoding="utf-8") as f:
                                tf.write(f.read())
                                tf.flush()
                        except FileNotFoundError:
                            # start with empty temp file
                            pass
                        finally:
                            tf.close()

                        # launch editor (this blocks until editor exits)
                        try:
                            subprocess.check_call([editor, tmpname])
                        except subprocess.CalledProcessError as e:
                            print(f"Editor exited with non-zero status: {e.returncode}")
                            return
                        except FileNotFoundError:
                            print(f"Editor not found: {editor}")
                            return

                        # read temp file and write back to target path
                        with open(tmpname, "r", encoding="utf-8") as tf_read:
                            new = tf_read.read()

                        target_dir = os.path.dirname(path)
                        if target_dir:
                            os.makedirs(target_dir, exist_ok=True)

                        with open(path, "w", encoding="utf-8") as out:
                            out.write(new)

                        print(f"Saved {path}")

                    finally:
                        try:
                            os.unlink(tmpname)
                        except Exception:
                            pass

                # run_in_terminal so the editor can take over the terminal
                run_in_terminal(_open_in_editor)

            elif cmd == "find" and len(cmd_parts) > 1:
                raw = cmd_parts[1]
                # support optional --ext flag: --ext .py or --ext py
                parts = raw.split()
                ext = None
                # support explicit flag --ext
                if "--ext" in parts:
                    i = parts.index("--ext")
                    if i + 1 < len(parts):
                        ext = parts[i + 1]
                        # remove ext flag and value from parts
                        del parts[i:i+2]

                # support implicit extension token anywhere: rs, py, cpp, c, js, ts, java
                known = {"rs", ".rs", "py", ".py", "cpp", ".cpp", "cc", ".cc", "c", ".c", "js", ".js", "ts", ".ts", "java", ".java"}
                remaining = []
                for tok in parts:
                    if tok.lower() in known and ext is None:
                        ext = tok
                        continue
                    remaining.append(tok)

                query = " ".join(remaining)
                print(cyan("\n🔎 Searching..."))
                matches = search_code(query, ext=ext)
                if not matches:
                    print(yellow("No results found."))
                for res in matches:
                    # support both (src, chunk) and (src, chunk, dist)
                    try:
                        src, chunk, dist = res
                    except ValueError:
                        try:
                            src, chunk = res[0], res[1]
                            dist = None
                        except Exception:
                            src, chunk, dist = None, str(res), None

                    print(green(f"\nFile: {src}"))
                    print(chunk)
                    if dist is not None:
                        print(magenta(f"Distance: {dist}"))
                    print("" + "-"*40)

            else:
                # unk command: try running it as a shell command.
                shell_cmd = q[1:].strip()
                if not shell_cmd:
                    print(f"Unknown command: {cmd}")
                    continue

                def _run_shell():
                    import subprocess
                    import os

                    shell = os.environ.get("SHELL", "/bin/sh")
                    try:
                        # use the user shell to execute the cmd string
                        subprocess.check_call(shell_cmd, shell=True, executable=shell)
                    except subprocess.CalledProcessError as e:
                        print(f"Command exited with code: {e.returncode}")
                    except FileNotFoundError:
                        print(f"Shell not found: {shell}")

                run_in_terminal(_run_shell)

        else:
            matches = search_code(q)
            # build context using available snippets 
            snippets = []
            for res in matches:
                try:
                    src, snippet, _ = res
                except ValueError:
                    try:
                        src, snippet = res[0], res[1]
                    except Exception:
                        src, snippet = None, str(res)
                snippets.append(f"File: {src}\n{snippet}")

            context = "\n\n".join(snippets)
            answer = await asyncio.to_thread(ask_model, q, context)

