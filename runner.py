import subprocess
import os
import shutil
import uuid

TEMP_DIR = os.path.join(os.path.dirname(__file__), "temp")
os.makedirs(TEMP_DIR, exist_ok=True)


def run_spectre(code: str, output: str = None, flags=None):
    if flags is None:
        flags = []

    file_id = str(uuid.uuid4())
    src_path = os.path.join(TEMP_DIR, f"{file_id}.sx")
    binary_path = output or os.path.join(TEMP_DIR, file_id)

    with open(src_path, "w", encoding="utf-8") as f:
        f.write(code)

    spectre_path = shutil.which("spectre")
    if spectre_path is None:
        raise FileNotFoundError("spectre was not found in PATH")

    cmd = [spectre_path, src_path]

    # optional flags
    cmd.extend(flags)

    cmd.extend(["-o", binary_path])

    try:
        compile_proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=5
        )

        if compile_proc.returncode != 0:
            return {
                "stdout": compile_proc.stdout,
                "stderr": compile_proc.stderr,
                "exit_code": compile_proc.returncode
            }

        if not os.path.exists(binary_path):
            raise FileNotFoundError(f"compiled binary was not created: {binary_path}")

        run_proc = subprocess.run(
            [binary_path],
            capture_output=True,
            text=True,
            timeout=5
        )

        stderr = "\n".join(part for part in (compile_proc.stderr, run_proc.stderr) if part)

        return {
            "stdout": run_proc.stdout,
            "stderr": stderr,
            "exit_code": run_proc.returncode
        }

    except subprocess.TimeoutExpired:
        return {
            "error": "Execution timed out"
        }

    finally:
        try:
            os.remove(src_path)
        except FileNotFoundError:
            pass

        if not output:
            try:
                os.remove(binary_path)
            except FileNotFoundError:
                pass
