import os
import re
import time
from datetime import datetime

from adb_utils import _run_adb_command, clean_serial_for_filename
from adb_connectors import AdbUsbConnector, AdbWifiConnector
from adb_automator import AdbAutomator

class MainCli:
    """
    Main CLI application class to manage ADB operations.
    """
    def __init__(self):
        self.usb_connector = AdbUsbConnector()
        self.wifi_connector = AdbWifiConnector()
        self.adb_automator = AdbAutomator()
        self.all_authorized_devices = [] # This will be populated by _update_device_lists

    def _update_device_lists(self):
        """Internal method to refresh the list of connected devices."""
        _, usb_msg, usb_serials = self.usb_connector.check_connection()
        _, wifi_msg, wifi_serials = self.wifi_connector.check_connection()

        self.all_authorized_devices = sorted(list(set(usb_serials + wifi_serials)))

        print("\n--- Current ADB Connection Status ---")
        print(f"USB Status: {usb_msg}")
        print(f"Wi-Fi Status: {wifi_msg}")
        if self.all_authorized_devices:
            print(f"Total Authorized Devices: {', '.join(self.all_authorized_devices)}")
        else:
            print("No authorized ADB devices (USB or Wi-Fi) found.")

        return bool(self.all_authorized_devices)

    def _select_target_device(self):
        """Prompts user to select a device if multiple are connected, or returns the single device."""
        if not self.all_authorized_devices:
            print("No authorized devices available to select.")
            return None

        if len(self.all_authorized_devices) == 1:
            selected_serial = self.all_authorized_devices[0]
            print(f"\nAutomatically selecting the only connected device: {selected_serial}")
            return selected_serial
        else:
            print("\nMultiple authorized devices found:")
            for i, serial in enumerate(self.all_authorized_devices):
                print(f"  {i+1}. {serial}")
            while True:
                try:
                    choice = int(input("Enter the number of the device to query: "))
                    if 1 <= choice <= len(self.all_authorized_devices):
                        return self.all_authorized_devices[choice - 1]
                    else:
                        print("Invalid choice. Please enter a number from the list.")
                except ValueError:
                    print("Invalid input. Please enter a number.")

    def _get_output_path(self, default_filename):
        """Prompts the user for a folder and constructs a full file path."""
        print("\n--- Save Output to File ---")
        while True:
            folder_path = input("Enter the folder path to save the output (e.g., C:\\MyReports or /home/user/adb_logs): ").strip()
            if not folder_path:
                print("Folder path cannot be empty. Please try again or press Ctrl+C to cancel.")
                continue

            expanded_path = os.path.expanduser(folder_path)

            try:
                if os.path.exists(expanded_path) and not os.path.isdir(expanded_path):
                    print(f"Error: Path '{expanded_path}' exists but is not a directory. Please choose a different path.")
                    continue
                os.makedirs(expanded_path, exist_ok=True)
                full_path = os.path.join(expanded_path, default_filename)
                return full_path
            except OSError as e:
                print(f"Error creating/accessing folder '{expanded_path}': {e}. Please try again.")
            except Exception as e:
                print(f"An unexpected error occurred with the path: {e}. Please try again.")

    def _save_to_file(self, content, filename):
        """Saves provided content to a file in a user-specified directory."""
        file_path = self._get_output_path(filename)
        if not file_path:
            return False, "File saving cancelled or path invalid."

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, f"Output successfully saved to: {file_path}"
        except IOError as e:
            return False, f"Error writing to file {file_path}: {e}"
        except Exception as e:
            return False, f"An unexpected error occurred during file saving: {e}"

    def _save_single_info_to_file(self, serial, data_name, data_content):
        """Prompts user to save specific data to a file."""
        if not data_content or data_content.strip() == "N/A (Error or not found)":
            print(f"No meaningful content to save for '{data_name}'. Skipping save prompt.")
            return

        save_choice = input(f"Do you want to save the '{data_name}' info to a file? (y/n): ").lower().strip()
        if save_choice == 'y':
            cleaned_serial = clean_serial_for_filename(serial)
            sanitized_data_name = re.sub(r'[^\w\-_\. ]', '', data_name).replace(' ', '_').lower()
            filename = f"adb_{cleaned_serial}_{sanitized_data_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            success, message = self._save_to_file(f"--- {data_name} for {serial} ({datetime.now().strftime('%Y-%m-%d %H-%M-%S')}) ---\n\n{data_content}", filename)
            print(message)

    # --- Logcat Methods ---
    def _dump_logcat_to_file(self, serial):
        """Dumps the logcat buffer for a device to a file, asking for output path."""
        print(f"\nAttempting to dump logcat for {serial} to a file...")
        stdout, stderr = _run_adb_command(['shell', 'logcat', '-d'], serial, raw_output=True)

        if stdout:
            print("Logcat dump successful. Now specify where to save it.")
            cleaned_serial = clean_serial_for_filename(serial)
            filename = f"adb_{cleaned_serial}_logcat_dump_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            success, message = self._save_to_file(f"--- Logcat Dump for {serial} ({datetime.now().strftime('%Y-%m-%d %H-%M-%S')}) ---\n\n{stdout}", filename)
            print(message)
        else:
            print(f"Error dumping logcat for {serial}: {stderr}")
            cleaned_serial = clean_serial_for_filename(serial)
            filename = f"adb_{cleaned_serial}_logcat_dump_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            success, message = self._save_to_file(f"--- Logcat Dump Error for {serial} ({datetime.now().strftime('%Y-%m-%d %H-%M-%S')}) ---\n\n{stderr}", filename)
            print(message)

    def _clear_logcat_buffer(self, serial):
        """Clears the logcat buffer for a device."""
        print(f"Attempting to clear logcat buffer for {serial}...")
        _, stderr = _run_adb_command(['shell', 'logcat', '-c'], serial)
        if not stderr:
            print(f"Logcat buffer cleared successfully for {serial}.")
        else:
            print(f"Error clearing logcat buffer: {stderr}")

    def logcat_menu(self, selected_device_serial):
        """Presents a menu for logcat operations."""
        while True:
            print(f"\n--- Logcat Operations for {selected_device_serial} ---")
            print("1. Dump Logcat to File (current buffer)")
            print("2. Clear Logcat Buffer")
            print("3. Return to Device Info Menu")

            choice = input("Enter your choice: ")

            if choice == '1':
                self._dump_logcat_to_file(selected_device_serial)
            elif choice == '2':
                self._clear_logcat_buffer(selected_device_serial)
            elif choice == '3':
                print("Exiting Logcat Operations.")
                break
            else:
                print("Invalid choice. Please enter a number between 1 and 3.")

    def get_device_info_menu(self):
        """Presents a menu for getting device information."""
        selected_device_serial = self._select_target_device()
        if not selected_device_serial:
            return

        while True:
            print(f"\n--- Device Info Menu for {selected_device_serial} ---")
            print("1. Get Device Model & Manufacturer")
            print("2. Get Detailed System Properties (getprop)")
            print("3. Show all network interfaces (ip addr)")
            print("4. Show Memory Usage by Process (procrank)")
            print("5. Get Memory Usage for Specific Application (dumpsys meminfo <package_name>)")
            print("6. Save ALL available Device Info to a single file")
            print("7. Logcat Operations")
            print("8. Exit to main menu")

            choice = input("Enter your choice: ")

            if choice == '1':
                model, err_model = _run_adb_command(['shell', 'getprop', 'ro.product.model'], selected_device_serial)
                manufacturer, err_manu = _run_adb_command(['shell', 'getprop', 'ro.product.manufacturer'], selected_device_serial)
                output_content = ""
                if model:
                    output_content += f"Device Model: {model}\n"
                    print(f"Device Model: {model}")
                else:
                    output_content += f"Error getting Device Model: {err_model}\n"
                    print(f"Error getting Device Model: {err_model}")
                if manufacturer:
                    output_content += f"Manufacturer: {manufacturer}\n"
                    print(f"Manufacturer: {manufacturer}")
                else:
                    output_content += f"Error getting Manufacturer: {err_manu}\n"
                    print(f"Error getting Manufacturer: {err_manu}")
                self._save_single_info_to_file(selected_device_serial, "Device Model & Manufacturer", output_content.strip())

            elif choice == '2':
                stdout, stderr = _run_adb_command(['shell', 'getprop'], selected_device_serial, raw_output=True)
                if stdout:
                    print("--- All System Properties ---")
                    print(stdout)
                    self._save_single_info_to_file(selected_device_serial, "System Properties", stdout)
                else:
                    print(f"Error getting System Properties: {stderr}")
                    self._save_single_info_to_file(selected_device_serial, "System Properties", stderr)

            elif choice == '3':
                stdout, stderr = _run_adb_command(['shell', 'ip', 'addr', 'show'], selected_device_serial, raw_output=True)
                if stdout:
                    print("--- Network Interfaces (ip addr) ---")
                    print(stdout)
                    self._save_single_info_to_file(selected_device_serial, "Network Interfaces", stdout)
                else:
                    print(f"Error getting Network Interfaces: {stderr}")
                    self._save_single_info_to_file(selected_device_serial, "Network Interfaces", stderr)

            elif choice == '4':
                print("\nFetching Procrank (Memory Usage by Process)...")
                test_procrank, _ = _run_adb_command(['shell', 'which', 'procrank'], selected_device_serial)
                if test_procrank:
                    output, stderr = _run_adb_command(['shell', 'procrank'], selected_device_serial, raw_output=True)
                    if output:
                        print("\n--- Procrank Output ---")
                        print(output)
                        self._save_single_info_to_file(selected_device_serial, "Procrank Memory Usage", output)
                    else:
                        print(f"Error getting procrank output: {stderr}")
                        self._save_single_info_to_file(selected_device_serial, "Procrank Memory Usage", f"Error: {stderr}")
                else:
                    msg = "Procrank command not found on this device. It might not be available or in the PATH."
                    print(msg)
                    print("Consider trying 'dumpsys meminfo' for detailed memory analysis (option 5).")
                    self._save_single_info_to_file(selected_device_serial, "Procrank Memory Usage", msg)

            elif choice == '5':
                package_name = input("Enter the application package name (e.g., com.android.chrome): ").strip()
                if not package_name:
                    print("Package name cannot be empty.")
                    continue
                print(f"\nFetching dumpsys meminfo for {package_name}...")
                stdout, stderr = _run_adb_command(['shell', 'dumpsys', 'meminfo', package_name], selected_device_serial, raw_output=True)
                if stdout:
                    print(f"\n--- Dumpsys Meminfo for {package_name} ---")
                    print(stdout)
                    self._save_single_info_to_file(selected_device_serial, f"Meminfo_{package_name}", stdout)
                else:
                    print(f"Error getting dumpsys meminfo for {package_name}: {stderr}")
                    self._save_single_info_to_file(selected_device_serial, f"Meminfo_{package_name}_Error", stderr)

            elif choice == '6':
                self._save_all_device_info(selected_device_serial)
            elif choice == '7':
                self.logcat_menu(selected_device_serial)
            elif choice == '8':
                print("Exiting Device Info Menu.")
                break
            else:
                print("Invalid choice. Please enter a number between 1 and 8.")

    def _save_all_device_info(self, serial):
        """Gathers all available device info and saves it to a single file."""
        print(f"\nGathering all information for {serial} to save to file...")
        info_content = f"--- Device Information for {serial} ({datetime.now().strftime('%Y-%m-%d %H-%M-%S')}) ---\n\n"

        info_commands = {
            "Device Model & Manufacturer": ['shell', 'getprop', 'ro.product.model', 'ro.product.manufacturer'],
            "System Properties (getprop)": ['shell', 'getprop'],
            "Network Interfaces (ip addr)": ['shell', 'ip', 'addr', 'show'],
            "Procrank Memory Usage": ['shell', 'procrank'],
            "Android Version": ['shell', 'getprop', 'ro.build.version.release'],
            "Battery Status (dumpsys battery)": ['shell', 'dumpsys', 'battery'],
            "Storage Usage (/sdcard)": ['shell', 'df', '-h', '/sdcard']
        }

        for name, cmd_args in info_commands.items():
            info_content += f"--- {name} ---\n"
            if name == "Device Model & Manufacturer":
                model, _ = _run_adb_command(['shell', 'getprop', 'ro.product.model'], serial)
                manufacturer, _ = _run_adb_command(['shell', 'getprop', 'ro.product.manufacturer'], serial)
                info_content += f"Model: {model if model else 'N/A (Error or not found)'}\n"
                info_content += f"Manufacturer: {manufacturer if manufacturer else 'N/A (Error or not found)'}\n"
            elif name == "Procrank Memory Usage":
                test_procrank, _ = _run_adb_command(['shell', 'which', 'procrank'], serial)
                if test_procrank:
                    output, _ = _run_adb_command(cmd_args, serial, raw_output=True)
                    info_content += f"{output if output else 'N/A (Error or no output)'}\n"
                else:
                    info_content += "N/A (Procrank command not found on this device)\n"
            else:
                output, _ = _run_adb_command(cmd_args, serial, raw_output=True)
                info_content += f"{output if output else 'N/A (Error or no output)'}\n"
            info_content += "\n"
        cleaned_serial = clean_serial_for_filename(serial)
        filename = f"adb_device_info_ALL_{cleaned_serial}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        success, message = self._save_to_file(info_content, filename)
        print(message)

    # --- Backup Methods ---
    def _backup_all_phone(self, serial):
        """Performs a full device backup."""
        print(f"\n--- Initiating Full Phone Backup for {serial} ---")
        print("\n!!! IMPORTANT !!!")
        print("You MUST look at your Android device NOW and CONFIRM the backup operation on its screen.")
        print("Without on-device confirmation, the backup WILL FAIL or hang.")
        print("This process can take a LONG time (minutes to hours) depending on device storage.")

        auto_confirm_choice = input("Attempt to automatically confirm and input password? (y/n): ").lower().strip()
        auto_confirm = auto_confirm_choice == 'y'

        password_to_use = ""
        tap_coords = None
        password_coords = None
        confirm_pass_coords = None

        if auto_confirm:
            print("\n!!! WARNING: Automatic confirmation is EXPERIMENTAL and UNRELIABLE. !!!")
            print("It requires precise screen coordinates, which vary by device/Android version.")
            print("You may need to manually provide them or it will likely fail.")
            print("Refer to AdbAutomator class comments for how to find coordinates.")

            use_provided_coords = input("Use the provided coordinates ? (y/n): ").lower().strip() == 'y'

            if use_provided_coords:
                tap_coords = (758, 1230)
                password_coords = (137, 790)
                confirm_pass_coords = (758, 1230)
                password_to_use = "1234"
                print("Using your provided coordinates and password '1234'.")
                print("BE PREPARED TO INTERVENE MANUALLY if this fails.")
            else:
                try:
                    tap_x = int(input("Enter X coordinate for 'Backup my data' tap (e.g., 758): "))
                    tap_y = int(input("Enter Y coordinate for 'Backup my data' tap (e.g., 1230): "))
                    tap_coords = (tap_x, tap_y)

                    password_input_x = int(input("Enter X coordinate for password input field (e.g., 137): "))
                    password_input_y = int(input("Enter Y coordinate for password input field (e.g., 790): "))
                    password_coords = (password_input_x, password_input_y)

                    confirm_pass_x = int(input("Enter X coordinate for password confirm button (e.g., 758): "))
                    confirm_pass_y = int(input("Enter Y coordinate for password confirm button (e.g., 1230): "))
                    confirm_pass_coords = (confirm_pass_x, confirm_pass_y)

                    password_to_use = input("Enter backup password (if any, leave blank for none): ").strip()
                except ValueError:
                    print("Invalid coordinate input. Reverting to manual confirmation.")
                    auto_confirm = False

        input("Press Enter to initiate backup (and be ready on device if not auto-confirming)...")

        cleaned_serial = clean_serial_for_filename(serial)
        default_filename = f"adb_backup_all_{cleaned_serial}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.ab"
        backup_file_path = self._get_output_path(default_filename)

        if not backup_file_path:
            print("Backup cancelled.")
            return

        print(f"Attempting to backup ALL data to: {backup_file_path}")
        print("Waiting for device confirmation and backup to complete...")

        try:
            full_command = ['adb']
            full_command.extend(['-s', serial])
            full_command.extend(['backup', '-all', '-f', backup_file_path])

            backup_process = subprocess.Popen(
                full_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            if auto_confirm:
                print("Attempting automatic confirmation in 5 seconds...")
                time.sleep(5)
                if tap_coords:
                    print(f"Attempting to tap 'Backup my data' at {tap_coords}...")
                    self.adb_automator.tap_screen(serial, tap_coords[0], tap_coords[1])
                    time.sleep(2)

                if password_to_use:
                    print(f"Attempting to input password '{password_to_use}'...")
                    if password_coords:
                        self.adb_automator.tap_screen(serial, password_coords[0], password_coords[1])
                        time.sleep(1)
                    self.adb_automator.input_text(serial, password_to_use)
                    time.sleep(1)
                    if confirm_pass_coords:
                        self.adb_automator.tap_screen(serial, confirm_pass_coords[0], confirm_pass_coords[1])
                    else:
                        self.adb_automator.press_key(serial, 66)
                    time.sleep(2)

            stdout, stderr = backup_process.communicate(timeout=3600)

            if backup_process.returncode == 0:
                print(f"\nSUCCESS: Full phone backup completed to {backup_file_path}")
                print("Remember to look at the file size to ensure data was backed up.")
            else:
                print(f"\nERROR: Full phone backup failed for {serial}.")
                print(f"ADB Stderr: {stderr.strip()}")
                print("Possible reasons: On-device confirmation not given, insufficient storage, ADB error, or device issues.")

        except subprocess.TimeoutExpired:
            backup_process.kill()
            stdout, stderr = backup_process.communicate()
            print(f"\nWARNING: Full phone backup timed out. This likely means the backup is very large or automation failed.")
            print(f"Please check {backup_file_path} for partial data or try again with a longer manual wait or increased timeout if this script was modified.")
            print(f"ADB Stderr (if any before timeout): {stderr.strip()}")
        except Exception as e:
            print(f"\nAn unexpected error occurred during backup: {e}")
            if 'backup_process' in locals() and backup_process.poll() is None:
                backup_process.kill()

    def _backup_specific_app(self, serial):
        """Performs a backup of a specific application."""
        package_name = input("Enter the application package name to backup (e.g., com.example.myapp): ").strip()
        if not package_name:
            print("Package name cannot be empty. Backup cancelled.")
            return

        print(f"\n--- Initiating Backup for App: {package_name} on {serial} ---")
        print("\n!!! IMPORTANT !!!")
        print("You MUST look at your Android device NOW and CONFIRM the backup operation on its screen.")
        print("Without on-device confirmation, the backup WILL FAIL or hang.")

        auto_confirm_choice = input("Attempt to automatically confirm and input password? (y/n): ").lower().strip()
        auto_confirm = auto_confirm_choice == 'y'

        password_to_use = ""
        tap_coords = None
        password_coords = None
        confirm_pass_coords = None

        if auto_confirm:
            print("\n!!! WARNING: Automatic confirmation is EXPERIMENTAL and UNRELIABLE. !!!")
            print("It requires precise screen coordinates, which vary by device/Android version.")
            print("You may need to manually provide them or it will likely fail.")

            use_provided_coords = input("Use the provided coordinates? (y/n): ").lower().strip() == 'y'

            if use_provided_coords:
                tap_coords = (758, 1230)
                password_coords = (137, 790)
                confirm_pass_coords = (758, 1230)
                password_to_use = "1234"
                print("Using your provided coordinates and password '1234'.")
                print("BE PREPARED TO INTERVENE MANUALLY if this fails.")
            else:
                try:
                    tap_x = int(input("Enter X coordinate for 'Backup my data' tap (e.g., 758): "))
                    tap_y = int(input("Enter Y coordinate for 'Backup my data' tap (e.g., 1230): "))
                    tap_coords = (tap_x, tap_y)

                    password_input_x = int(input("Enter X coordinate for password input field (e.g., 137): "))
                    password_input_y = int(input("Enter Y coordinate for password input field (e.g., 790): "))
                    password_coords = (password_input_x, password_input_y)

                    confirm_pass_x = int(input("Enter X coordinate for password confirm button (e.g., 758): "))
                    confirm_pass_y = int(input("Enter Y coordinate for password confirm button (e.g., 1230): "))
                    confirm_pass_coords = (confirm_pass_x, confirm_pass_y)

                    password_to_use = input("Enter backup password (if any, leave blank for none): ").strip()
                except ValueError:
                    print("Invalid coordinate input. Reverting to manual confirmation.")
                    auto_confirm = False

        input("Press Enter to initiate backup (and be ready on device if not auto-confirming)...")

        cleaned_serial = clean_serial_for_filename(serial)
        sanitized_package_name = re.sub(r'[^\w\.]', '', package_name)
        default_filename = f"adb_backup_app_{sanitized_package_name}_{cleaned_serial}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.ab"
        backup_file_path = self._get_output_path(default_filename)

        if not backup_file_path:
            print("Backup cancelled.")
            return

        print(f"Attempting to backup {package_name} to: {backup_file_path}")
        print("Waiting for device confirmation and backup to complete...")

        try:
            full_command = ['adb']
            full_command.extend(['-s', serial])
            full_command.extend(['backup', '-f', backup_file_path, '-apk', package_name])

            backup_process = subprocess.Popen(
                full_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            if auto_confirm:
                print("Attempting automatic confirmation in 5 seconds...")
                time.sleep(5)
                if tap_coords:
                    print(f"Attempting to tap 'Backup my data' at {tap_coords}...")
                    self.adb_automator.tap_screen(serial, tap_coords[0], tap_coords[1])
                    time.sleep(2)

                if password_to_use:
                    print(f"Attempting to input password '{password_to_use}'...")
                    if password_coords:
                        self.adb_automator.tap_screen(serial, password_coords[0], password_coords[1])
                        time.sleep(1)
                    self.adb_automator.input_text(serial, password_to_use)
                    time.sleep(1)
                    if confirm_pass_coords:
                        self.adb_automator.tap_screen(serial, confirm_pass_coords[0], confirm_pass_coords[1])
                    else:
                        self.adb_automator.press_key(serial, 66)
                    time.sleep(2)

            stdout, stderr = backup_process.communicate(timeout=600)

            if backup_process.returncode == 0:
                print(f"\nSUCCESS: Backup for {package_name} completed to {backup_file_path}")
                print("Remember to look at the file size to ensure data was backed up.")
            else:
                print(f"\nERROR: Backup for {package_name} failed for {serial}.")
                print(f"ADB Stderr: {stderr.strip()}")
                print("Possible reasons: App doesn't allow backup, on-device confirmation not given, app not found, or device issues.")

        except subprocess.TimeoutExpired:
            backup_process.kill()
            stdout, stderr = backup_process.communicate()
            print(f"\nWARNING: Backup for {package_name} timed out. This might happen for very large apps or automation failed.")
            print(f"Please check {backup_file_path} for partial data or try again with a longer manual wait.")
            print(f"ADB Stderr (if any before timeout): {stderr.strip()}")
        except Exception as e:
            print(f"\nAn unexpected error occurred during app backup: {e}")
            if 'backup_process' in locals() and backup_process.poll() is None:
                backup_process.kill()

    def _list_all_applications(self, serial):
        """Lists all installed applications on the device and offers to save to file."""
        print(f"\n--- Listing all installed applications on {serial} ---")
        stdout, stderr = _run_adb_command(['shell', 'pm', 'list', 'packages', '-f'], serial, raw_output=True)

        if stdout:
            app_list_raw = stdout.strip().split('\n')
            parsed_app_list = []
            for line in app_list_raw:
                match = re.match(r'package:([^\s]+)=(.+)', line)
                if match:
                    apk_path = match.group(1)
                    package_name = match.group(2)
                    parsed_app_list.append(f"Package: {package_name}, APK Path: {apk_path}")
                else:
                    parsed_app_list.append(line.strip())

            output_content = "\n".join(parsed_app_list)
            print("\n--- Installed Applications ---")
            print(output_content)
            self._save_single_info_to_file(serial, "Installed Applications List", output_content)
        else:
            print(f"Error listing applications for {serial}: {stderr}")
            self._save_single_info_to_file(serial, "Installed Applications List Error", stderr)

    def backup_menu(self):
        """Presents a menu for backup operations."""
        selected_device_serial = self._select_target_device()
        if not selected_device_serial:
            return

        while True:
            print(f"\n--- Backup Operations for {selected_device_serial} ---")
            print("1. Backup All Phone Data")
            print("2. Backup Specific Application Data")
            print("3. List All Installed Applications")
            print("4. Return to Main Menu")

            choice = input("Enter your choice: ")

            if choice == '1':
                self._backup_all_phone(selected_device_serial)
            elif choice == '2':
                self._backup_specific_app(selected_device_serial)
            elif choice == '3':
                self._list_all_applications(selected_device_serial)
            elif choice == '4':
                print("Exiting Backup Operations.")
                break
            else:
                print("Invalid choice. Please enter a number between 1 and 4.")

    def usb_connection_menu(self):
        """Presents a menu for managing USB ADB connections."""
        while True:
            print("\n--- USB ADB Connection Management ---")
            print("1. Check USB Device Connection Status (Refresh)")
            print("2. Return to Main Menu")

            choice = input("Enter your choice: ")

            if choice == '1':
                is_connected, message, authorized_serials = self.usb_connector.check_connection()
                print(f"\n--- USB Connection Check Result ---")
                print(message)
                if authorized_serials:
                    print(f"Currently connected and authorized USB device(s): {', '.join(authorized_serials)}")
                if not is_connected and "unauthorized" in message:
                    print("\nACTION REQUIRED: Please check your Android device screen and authorize USB debugging.")
                elif not is_connected and "offline" in message:
                    print("\nACTION REQUIRED: Ensure your device is powered on and not in a special mode (e.g., fastboot).")
                print("------------------------------------")
                self._update_device_lists()
            elif choice == '2':
                print("Exiting USB ADB Connection Management.")
                break
            else:
                print("Invalid choice. Please enter 1 or 2.")

    def wifi_connection_menu(self):
        """Presents a menu for managing Wi-Fi ADB connections."""
        while True:
            print("\n--- Wi-Fi ADB Connection Management ---")
            print("1. Check Wi-Fi Device Connection Status (Refresh)")
            print("2. Connect to Device via IP and Port")
            print("3. Pair Device Wirelessly (Android 11+)")
            # Removed option 4: "4. Set USB-Connected Device to TCP/IP Mode (for Wi-Fi Debugging)"
            print("4. Disconnect Specific Wi-Fi Device (by IP:Port)") # This was 5, now 4
            print("5. Disconnect ALL Wi-Fi Devices") # This was 6, now 5
            print("6. Return to Main Menu") # This was 7, now 6

            choice = input("Enter your choice: ")

            if choice == '1':
                _, msg, _ = self.wifi_connector.check_connection()
                print(f"\n--- Wi-Fi Connection Check Result ---")
                print(msg)
                print("------------------------------------")
                self._update_device_lists()

            elif choice == '2':
                ip_port = input("Enter device IP and port (e.g., 192.168.1.100:5555): ").strip()
                if not ip_port:
                    print("IP and port cannot be empty.")
                    continue
                success, message = self.wifi_connector.connect_device_ip_port(ip_port)
                print(f"\nConnection attempt: {message}")
                self._update_device_lists()

            elif choice == '3':
                ip = input("Enter device IP for pairing (e.g., 192.168.1.100): ").strip()
                port = input("Enter pairing port (usually 37817, found on device Wireless Debugging screen): ").strip()
                pairing_code = input("Enter pairing code (e.g., 123456, found on device Wireless Debugging screen): ").strip()

                if not all([ip, port, pairing_code]):
                    print("All pairing details are required.")
                    continue
                success, message = self.wifi_connector.pair_device_wireless(ip, port, pairing_code)
                print(f"\nPairing attempt: {message}")
                self._update_device_lists()

            # Removed the logic for choice '4' (Set TCP/IP Mode)
            # elif choice == '4':
            #     # This block is removed

            elif choice == '4': # This was '5', now it's '4'
                ip_port_to_disconnect = input("Enter the IP and port of the device to disconnect (e.g., 192.168.1.100:5555): ").strip()
                if not ip_port_to_disconnect:
                    print("IP and port cannot be empty.")
                    continue
                success, message = self.wifi_connector.disconnect_device_ip(ip_port_to_disconnect)
                print(f"\nDisconnect attempt: {message}")
                self._update_device_lists()

            elif choice == '5': # This was '6', now it's '5'
                confirm = input("Are you sure you want to disconnect ALL Wi-Fi ADB devices? (y/n): ").lower().strip()
                if confirm == 'y':
                    success, message = self.wifi_connector.disconnect_all_wifi()
                    print(f"\nDisconnect all attempt: {message}")
                    self._update_device_lists()
                else:
                    print("Disconnect all cancelled.")

            elif choice == '6': # This was '7', now it's '6'
                print("Exiting Wi-Fi ADB Connection Management.")
                break
            else:
                print("Invalid choice. Please enter a number between 1 and 6.") # Updated range

    def main_menu(self):
        """Displays the main menu and handles user input."""
        while True:
            self._update_device_lists()

            print("\n--- ADB Utility Main Menu ---")
            print("1. Check/Manage USB ADB Connections")
            print("2. Manage Wi-Fi ADB Connections")
            print("3. Get Device Information / Query Device")
            print("4. Perform Device Backup")
            print("5. Exit")

            choice = input("Enter your choice: ")

            if choice == '1':
                self.usb_connection_menu()
            elif choice == '2':
                self.wifi_connection_menu()
            elif choice == '3':
                if self.all_authorized_devices:
                    self.get_device_info_menu()
                else:
                    print("No authorized devices found. Please connect and authorize a device first.")
            elif choice == '4':
                if self.all_authorized_devices:
                    self.backup_menu()
                else:
                    print("No authorized devices found. Please connect and authorize a device first.")
            elif choice == '5':
                print("Exiting ADB Utility. Goodbye!")
                break
            else:
                print("Invalid choice. Please enter a number between 1 and 5.")

if __name__ == "__main__":
    cli = MainCli()
    cli.main_menu()