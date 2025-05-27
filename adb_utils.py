import subprocess
import re
from datetime import datetime

# Constants for better readability
ADB_COMMAND = 'adb'
TIMEOUT_SECONDS = 30 # Default timeout for most ADB commands
WIFI_SERIAL_PATTERN = r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+$'

# --- Helper Function for ADB Command Execution ---
def _run_adb_command(command_args, target_serial=None, raw_output=False, timeout=TIMEOUT_SECONDS):
    """
    Internal helper to run an ADB command and return its stdout and stderr.
    Optionally targets a specific device by serial number.
    If raw_output is True, returns stdout and stderr as is, without stripping.
    Includes a configurable timeout.
    """
    full_command = [ADB_COMMAND]
    if target_serial:
        full_command.extend(['-s', target_serial])
    full_command.extend(command_args)

    try:
        result = subprocess.run(
            full_command,
            capture_output=True,
            text=True,
            check=True,
            timeout=timeout,
            encoding='utf-8',
            errors='replace'
        )
        return result.stdout if raw_output else result.stdout.strip(), result.stderr.strip()
    except FileNotFoundError:
        return None, f"Error: '{ADB_COMMAND}' command not found. Please ensure ADB is installed and added to your system's PATH."
    except subprocess.CalledProcessError as e:
        return None, f"Error executing command: {' '.join(full_command)}\nStderr: {e.stderr.strip()}"
    except subprocess.TimeoutExpired:
        return None, f"Error: Command timed out after {timeout} seconds: {' '.join(full_command)}"
    except Exception as e:
        return None, f"An unexpected error occurred: {e}"

def clean_serial_for_filename(serial):
    """Removes the port number from a Wi-Fi serial (IP:Port) for use in filenames."""
    if re.match(WIFI_SERIAL_PATTERN, serial):
        return serial.split(':')[0] # Return just the IP
    return serial # Return as is for USB serials