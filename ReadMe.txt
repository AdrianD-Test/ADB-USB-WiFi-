This Python-based ADB Utility provides a command-line interface to streamline common Android Debug Bridge operations. It allows users to manage USB and Wi-Fi device connections, retrieve detailed device information, perform full or app-specific backups (with experimental automation features), and interact with logcat, all through a user-friendly menu system.

The ADB Utility script offers several functionalities that can be valuable in digital forensic analysis of Android devices:

Data Acquisition (Backups):

Full Phone Backup: The ability to perform a full device backup (adb backup) is crucial for acquiring a comprehensive image of user data, application data, and device settings. While it creates a .ab file (Android Backup) which needs to be parsed, this is a foundational step in many forensic investigations to preserve evidence.
Specific Application Backup: Being able to back up individual application data can be extremely useful for targeted investigations. Many important artifacts (chats, user activity logs, cached data) reside within specific app data directories. This allows forensicators to isolate and analyze data from apps of interest without necessarily acquiring the entire device.
Device Information Gathering:

System Properties (getprop): Forensicators can use this to quickly gather critical device metadata such as Android version, build number, manufacturer, device model, security patch level, and various system configurations. This information is vital for understanding the device's environment and for contextualizing other findings.
Network Interfaces (ip addr): Information about network configurations, active IP addresses, and MAC addresses can help in reconstructing network activity, identifying connected networks, and tracing communication patterns.
Memory Usage (procrank, dumpsys meminfo): While primarily for performance analysis, these dumps can sometimes reveal running processes and their memory footprint, which might indicate active malicious processes or processes that were recently active. For specific apps, dumpsys meminfo can help in understanding resource consumption and potential artifacts left in memory.
Activity and Event Logging (Logcat Dumps):

Logcat Analysis: Logcat provides a chronological record of system events, application activities, errors, and debugging messages. This log can contain valuable forensic artifacts, including:
Application crashes or unusual behavior.
User interactions (e.g., app launches, screen unlocks).
Network connection attempts.
Security-related events or warnings.
Evidence of malware activity or system tampering.
Clearing Logcat Buffer: The option to clear the logcat buffer before an action could theoretically be used to isolate logs specific to a new activity, although in a strict forensic context, clearing logs is generally avoided unless performing controlled tests.
Application Listing:

Installed Applications (pm list packages): Getting a complete list of installed applications, along with their package names and APK paths, is fundamental for identifying potentially malicious applications, unauthorized software, or applications relevant to the case. This helps in understanding the attack surface and potential sources of evidence.
