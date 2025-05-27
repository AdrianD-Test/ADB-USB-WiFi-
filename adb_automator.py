from adb_utils import _run_adb_command

# --- AdbAutomator Class ---
class AdbAutomator:
    """
    Provides experimental methods to automate interaction with device screen
    for tasks like backup confirmation or password input.
    WARNING: These methods are highly device-dependent, Android version-dependent,
    and may not work reliably due to security measures or UI variations.
    Coordinates (x, y) are specific to your device's resolution and UI layout.
    """
    def __init__(self):
        pass

    def _shell_input(self, serial, command_type, value1, value2=None):
        """Internal helper for adb shell input commands."""
        cmd = ['shell', 'input', command_type, str(value1)]
        if value2 is not None:
            cmd.append(str(value2))
        _, stderr = _run_adb_command(cmd, serial)
        if stderr:
            print(f"Warning: AdbAutomator command failed: {' '.join(cmd)}\nStderr: {stderr}")
            return False
        return True

    def tap_screen(self, serial, x, y):
        """
        Attempts to tap on the screen at specified coordinates.
        x, y: pixel coordinates on the device screen.
        """
        # Convert to int as adb shell input tap expects integers
        x = int(x)
        y = int(y)
        print(f"Attempting to tap at ({x}, {y}) on {serial}...")
        return self._shell_input(serial, 'tap', x, y)

    def input_text(self, serial, text):
        """
        Attempts to input text into a focused text field.
        WARNING: This is often blocked for system-level password prompts.
        """
        print(f"Attempting to input text: '{text}' on {serial}...")
        # Escape spaces and special characters for adb shell input text
        escaped_text = text.replace(' ', '%s') # Simple space escaping
        return self._shell_input(serial, 'text', escaped_text)

    def press_key(self, serial, key_code):
        """
        Attempts to simulate a key press (e.g., ENTER).
        key_code: Android key event code (e.g., 66 for ENTER).
        """
        print(f"Attempting to press key code {key_code} on {serial}...")
        return self._shell_input(serial, 'keycode', key_code)