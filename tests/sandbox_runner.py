import subprocess
import sys
from pathlib import Path

def run_script(script_path: str):
    script_file = Path(script_path).resolve()
    if not script_file.exists():
        print(f"Error: Script {script_file} does not exist.")
        sys.exit(1)

    print(f"Running script: {script_file}")

    try:
        result = subprocess.run(
            [sys.executable, str(script_file)],
            capture_output=True,
            text=True,
            check=False
        )

        if result.stdout:
            print("--- STDOUT ---")
            print(result.stdout)

        if result.stderr:
            print("--- STDERR ---")
            print(result.stderr)

        if result.returncode != 0:
            print(f"CRITICAL FAILURE: {script_file} exited with code {result.returncode}")
            raise SystemExit(f"Execution failed for {script_file}")

        print(f"SUCCESS: {script_file} executed successfully.")

    except Exception as e:
        print(f"CRITICAL FAILURE: Exception while running {script_file}: {e}")
        raise SystemExit(f"Execution failed for {script_file}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python sandbox_runner.py <path_to_script>")
        sys.exit(1)

    run_script(sys.argv[1])
