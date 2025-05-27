import re
from adb_utils import _run_adb_command, WIFI_SERIAL_PATTERN

# --- AdbUsbConnector Class ---
class AdbUsbConnector:
    """
    Handles ADB connections specifically over USB.
    """
    def check_connection(self):
        """
        Checks for USB-connected and authorized ADB devices.
        Returns: (bool, str, list) - (True if good, message, list of authorized serials).
        """
        stdout, stderr = _run_adb_command(['devices'])
        if stderr:
            return False, f"Error running 'adb devices': {stderr}", []

        authorized_devices = []
        unauthorized_devices = []
        offline_devices = []

        # Start from the second line to skip "List of devices attached" header
        for line in stdout.strip().split('\n')[1:]:
            if not line.strip(): # Skip empty lines
                continue

            parts = line.split('\t')
            if len(parts) == 2:
                serial = parts[0].strip()
                status = parts[1].strip()

                # Filter out Wi-Fi devices for USB check
                if not re.match(WIFI_SERIAL_PATTERN, serial):
                    if status == 'device':
                        authorized_devices.append(serial)
                    elif status == 'unauthorized':
                        unauthorized_devices.append(serial)
                    elif status == 'offline':
                        offline_devices.append(serial)
                    else:
                        print(f"Warning: Unknown USB device status for serial '{serial}': {status}")

        if authorized_devices:
            return True, f"ADB USB connection successful. Device(s) connected and authorized: {', '.join(authorized_devices)}", authorized_devices
        elif unauthorized_devices:
            return False, f"Device(s) detected but 'unauthorized': {', '.join(unauthorized_devices)}. Please check your Android device and authorize the connection (allow USB debugging).", []
        elif offline_devices:
            return False, f"Device(s) detected but 'offline': {', '.join(offline_devices)}. Please ensure your device is powered on and not in a special mode.", []
        else:
            return False, "No authorized USB Android devices found.", []

# --- AdbWifiConnector Class ---
class AdbWifiConnector:
    """
    Handles ADB connections specifically over Wi-Fi.
    """
    def check_connection(self):
        """
        Checks for Wi-Fi connected and authorized ADB devices.
        Returns: (bool, str, list) - (True if good, message, list of authorized serials).
        """
        stdout, stderr = _run_adb_command(['devices'])
        if stderr:
            return False, f"Error running 'adb devices': {stderr}", []

        authorized_devices = []
        unauthorized_devices = []
        offline_devices = []

        # Start from the second line to skip "List of devices attached" header
        for line in stdout.strip().split('\n')[1:]:
            if not line.strip(): # Skip empty lines
                continue

            parts = line.split('\t')
            if len(parts) == 2:
                serial = parts[0].strip()
                status = parts[1].strip()

                # Filter for Wi-Fi devices based on IP:Port pattern
                if re.match(WIFI_SERIAL_PATTERN, serial):
                    if status == 'device':
                        authorized_devices.append(serial)
                    elif status == 'unauthorized':
                        unauthorized_devices.append(serial)
                    elif status == 'offline':
                        offline_devices.append(serial)
                    else:
                        print(f"Warning: Unknown Wi-Fi device status for serial '{serial}': {status}")

        if authorized_devices:
            return True, f"ADB Wi-Fi connection successful. Device(s) connected and authorized: {', '.join(authorized_devices)}", authorized_devices
        elif unauthorized_devices:
            return False, f"Wi-Fi Device(s) detected but 'unauthorized': {', '.join(unauthorized_devices)}. Check device for authorization prompt.", []
        elif offline_devices:
            return False, f"Wi-Fi Device(s) detected but 'offline': {', '.join(offline_devices)}. Check device and network.", []
        else:
            return False, "No authorized Wi-Fi Android devices found.", []

    def connect_device_ip_port(self, ip_port):
        """Attempts to connect to a device via its IP and port."""
        print(f"Attempting to connect to {ip_port}...")
        stdout, stderr = _run_adb_command(['connect', ip_port])
        if stdout and ("connected to" in stdout or "already connected" in stdout):
            print(f"Connection attempt output: {stdout.strip()}")
            return True, stdout
        else:
            return False, stderr

    def pair_device_wireless(self, ip, port, pairing_code):
        """Attempts to pair a device using the Android 11+ wireless debugging pairing code."""
        print(f"Attempting to pair with {ip}:{port} using code {pairing_code}...")
        print("\nNOTE: ADB pairing often requires interactive input in the terminal.")
        print(f"Please run the following command MANUALLY in your terminal if this fails:")
        print(f"  adb pair {ip}:{port}")
        print(f"And then enter the pairing code: {pairing_code}\n")

        stdout, stderr = _run_adb_command(['pair', f"{ip}:{port}"])
        if stdout and "Successfully paired" in stdout:
            print(f"Pairing command output: {stdout.strip()}")
            return True, stdout
        elif stdout:
            print(f"Pairing command output: {stdout.strip()}")
            print("If you were prompted for a code, you might need to run the manual command above.")
            return False, stdout
        else:
            return False, stderr

    # Removed the set_tcpip_mode method
    # def set_tcpip_mode(self, port="5555"):
    #     """Sets a USB-connected device to listen for ADB over TCP/IP."""
    #     print(f"Attempting to set device to listen on TCP/IP port {port}...")
    #     print("NOTE: Device must be connected via USB for this to work!")
    #     stdout, stderr = _run_adb_command(['tcpip', str(port)])
    #     if stdout and "restarting in TCP mode" in stdout:
    #         print(f"Device TCP/IP mode response: {stdout.strip()}")
    #         print("Now you can disconnect USB and use 'Connect to device via IP' option.")
    #         return True, stdout
    #     else:
    #         return False, stderr

    def disconnect_device_ip(self, ip_port):
        """Disconnects from a specific Wi-Fi ADB device."""
        print(f"Attempting to disconnect from {ip_port}...")
        stdout, stderr = _run_adb_command(['disconnect', ip_port])
        if stdout and "disconnected" in stdout:
            print(f"Successfully disconnected: {stdout.strip()}")
            return True, stdout
        else:
            return False, stderr

    def disconnect_all_wifi(self):
        """Disconnects all Wi-Fi ADB devices."""
        print("Attempting to disconnect all Wi-Fi ADB devices...")
        stdout, stderr = _run_adb_command(['disconnect'])
        if stdout and "disconnected" in stdout:
            print(f"Successfully disconnected all: {stdout.strip()}")
            return True, stdout
        else:
            return False, stderr