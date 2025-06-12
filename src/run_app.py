import multiprocessing
import subprocess
import sys
import time
import webbrowser
from pathlib import Path


def get_streamlit_command_and_path():
    """
    Określa prawidłowe polecenie do uruchomienia Streamlit i ścieżkę bazową dla zasobów.
    """
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        base_path = Path(sys._MEIPASS)
        streamlit_executable = str(base_path / 'streamlit')
        return streamlit_executable, base_path
    else:
        streamlit_executable = 'streamlit'
        base_path = Path(__file__).resolve().parent
        return streamlit_executable, base_path


def run_streamlit_app():
    """
    Uruchamia aplikację Streamlit w podprocesie.
    """
    streamlit_exe, base_path = get_streamlit_command_and_path()

    main_script_path = base_path / "src" / "presentation" / "app.py"

    url = "http://localhost:8501"

    command = [
        streamlit_exe,
        "run",
        str(main_script_path),
        "--server.port", "8501",
        "--server.headless", "true",
    ]

    print("--- PyInstaller Launcher ---")
    print(f"  > Base Path:      {base_path}")
    print(f"  > App Script:     {main_script_path}")
    print(f"  > Full Command:   {' '.join(command)}")
    print("----------------------------")

    proc = subprocess.Popen(command)

    print("\nWaiting for Streamlit server to start...")
    time.sleep(8)

    print(f"Opening browser to {url}")
    webbrowser.open(url)

    try:
        proc.wait()
    except KeyboardInterrupt:
        print("\nShutting down Streamlit server...")
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()

    print("--- Launcher script finished. ---")


if __name__ == "__main__":
    multiprocessing.freeze_support()
    run_streamlit_app()
