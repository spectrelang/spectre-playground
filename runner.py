import subprocess
import os
import shutil
import uuid

TEMP_DIR = os.path.join(os.path.dirname(__file__), "temp")
os.makedirs(TEMP_DIR, exist_ok=True)
EXECUTION_TIMEOUT_SECONDS = 7


class SecurityViolation(ValueError):
    pass


FORBIDDEN_SUBSTRINGS = (
    ("std/os", 'Imports of "std/os" are not allowed.'),
    ("std/fs", 'Imports of "std/fs" are not allowed.'),
    ("std/reflection", 'Imports of "std/reflection" are not allowed.'),
    (".os.", "Access to std.os is not allowed."),
    (".fs.", "Access to std.fs is not allowed."),
    (".reflection.", "Access to std.reflection is not allowed."),
    ("extern", "Extern declarations are not allowed."),
    ('link "', "Link directives are not allowed."),
    ("link '", "Link directives are not allowed."),
)


def validate_code_security(code: str) -> None:
    for forbidden_substring, message in FORBIDDEN_SUBSTRINGS:
        if forbidden_substring in code:
            raise SecurityViolation(message)


def run_spectre(code: str, output: str = None, flags=None):
    if flags is None:
        flags = []

    if output not in (None, ""):
        raise SecurityViolation("Custom output paths are not allowed.")

    if flags:
        raise SecurityViolation("Custom compiler flags are not allowed.")

    validate_code_security(code)

    file_id = str(uuid.uuid4())
    src_path = os.path.join(TEMP_DIR, f"{file_id}.sx")
    binary_path = os.path.join(TEMP_DIR, file_id)

    with open(src_path, "w", encoding="utf-8") as f:
        f.write(code)

    spectre_path = shutil.which("spectre")
    if spectre_path is None:
        raise FileNotFoundError("spectre was not found in PATH")

    cmd = [spectre_path, src_path]

    cmd.extend(flags)

    cmd.extend(["-o", binary_path])

    try:
        compile_proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=EXECUTION_TIMEOUT_SECONDS
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
            timeout=EXECUTION_TIMEOUT_SECONDS
        )

        stderr = "\n".join(part for part in (compile_proc.stderr, run_proc.stderr) if part)

        return {
            "stdout": run_proc.stdout,
            "stderr": stderr,
            "exit_code": run_proc.returncode
        }

    except subprocess.TimeoutExpired as exc:
        timed_out_command = exc.cmd[0] if exc.cmd else ""
        phase = "Compilation" if timed_out_command == spectre_path else "Execution"
        return {
            "error": f"{phase} timed out after {EXECUTION_TIMEOUT_SECONDS} seconds"
        }

    finally:
        try:
            os.remove(src_path)
        except FileNotFoundError:
            pass

        try:
            os.remove(binary_path)
        except FileNotFoundError:
            pass
