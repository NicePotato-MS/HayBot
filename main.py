import configparser
import os
import subprocess
import colorama
import time
from datetime import datetime

# HayBot
HB_VERSION_MAJOR = 1
HB_VERSION_MINOR = 0
HB_VERSION_PATCH = 0

# Initialize colorama to work on both Windows and non-Windows systems
colorama.init(autoreset=True)

def fancyprint(message, color='white', log=True):
    # Get the current date and time
    current_date = datetime.now().strftime('%Y-%m-%d')
    current_time = datetime.now().strftime('%H-%M-%S')

    # Define color codes
    colors = {
        'black': colorama.Fore.BLACK,
        'red': colorama.Fore.RED,
        'green': colorama.Fore.GREEN,
        'yellow': colorama.Fore.YELLOW,
        'blue': colorama.Fore.BLUE,
        'magenta': colorama.Fore.MAGENTA,
        'cyan': colorama.Fore.CYAN,
        'white': colorama.Fore.WHITE
    }

    # Check if the provided color is valid; otherwise, default to white
    message_color = colors.get(color.lower(), colorama.Fore.WHITE)

    # Print the formatted message with time and specified color
    log_message = f"[{current_time}] {message}"
    print(f"{colorama.Fore.GREEN}[{current_time}] {message_color}{message}")

    # Log the message to the file if log=True
    if log:
        log_dir = os.path.join('logs')
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        log_dir_name = os.path.join(log_dir, f"HayBot-{current_date}-{current_time}")
        if not os.path.exists(log_dir_name):
            os.makedirs(log_dir_name)
        log_file_path = os.path.join(log_dir_name, f"haybot.log")
        with open(log_file_path, 'a') as log_file:
            log_file.write(f"{log_message}\n")

# Load config.ini
config_path = os.path.join(os.path.dirname(__file__), 'config.ini')
config = configparser.ConfigParser()
config.read(config_path)
# Pull out config from file
DEVICE_SERIAL = config.get('Android', 'serial')
DEVICE_USER = config.get('Android','user')
DEVICE_PACKAGE = config.get('Android','package')
OS_ADB = config.get('Android', 'adb-command')

def exec_adb(command):
    try:
        result = subprocess.run([f"{OS_ADB} {command}"], shell=True, capture_output=True, text=True)
        return result
    except FileNotFoundError:
        fancyprint("ADB command not found. Please make sure you have your config set up!","red")
        exit(-1)

def exec_device(command): # Execute on given device
    return exec_adb(f"-s {DEVICE_SERIAL} {command}")

def exec_shell(command): # Execute on the device's shell
    return exec_device(f"shell {command}")

def check_connected():
    result = exec_adb("devices")
    output_lines = result.stdout.strip().split('\n')[1:]

    connected = False

    for line in output_lines:
        if line.strip():
            device_info = line.strip().split('\t')
            if len(device_info) >= 2 and device_info[0] == DEVICE_SERIAL and device_info[1] == 'device':
                connected = True

    if not connected:
        fancyprint("Device is not connected. Please make sure you have your config set up!","red")
        exit(-2)
    
def check_power():
    output = exec_shell("dumpsys deviceidle").stdout
    # Parse the output to extract mScreenOn and mScreenLocked values
    mScreenOn = None
    mScreenLocked = None
    for line in output.splitlines():
        if line.strip().startswith("mScreenOn="):
            mScreenOn = line.strip().split("=")[1]
        elif line.strip().startswith("mScreenLocked="):
            mScreenLocked = line.strip().split("=")[1]    
    if mScreenOn is None or mScreenLocked is None:
        fancyprint("Android API is out of date. Are you running API 23 or more?","red")
        exit(-100)
    if mScreenOn == "false" or mScreenLocked == "true":
        fancyprint("Your device is off or locked, please turn it on and unlock it.","red")
        exit(-3)
    
def is_package_installed(package_name):
    # Use the 'pm list packages' command with --user option to check if the package is installed
    output = exec_shell(f"pm list packages --user {DEVICE_USER} {package_name}").stdout
    if output:
        return package_name in output.split("\n")
    else:
        return False
    
def check_ok():
    check_connected()
    check_power()

# Main
print(exec_shell("pm list packages --user 0 com.supercell.hayday").stdout)
check_ok()
fancyprint(f"HayBot has started! Version {HB_VERSION_MAJOR}.{HB_VERSION_MINOR}.{HB_VERSION_PATCH}","yellow")

exec_shell(f"input touchscreen swipe 500 500 600 600 500")
# Sleep for a short time to allow the first swipe to be processed
time.sleep(0.1)
# Start the pinch zoom in (zoom in)
exec_shell(f"input touchscreen swipe 800 800 700 700 500")
