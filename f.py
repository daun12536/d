import requests
import random
import string
import time
import threading
import queue

# --- Constants ---
NAMES = 10          # Amount of usernames to save
LENGTH = 5          # Length of usernames
FILE = 'valid_numeric.txt' # Automatically creates file
BIRTHDAY = '1999-04-20'  # User's birthday for validation
DEBUG = True       # Set to True for verbose output, False for clean output
NUM_THREADS = 5    # Number of concurrent threads to run

# --- Color formatting for terminal output ---
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    GRAY = '\033[90m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# --- Thread-safe Shared Resources ---
task_queue = queue.Queue()
found_lock = threading.Lock()
found_count = 0

# --- Helper Functions ---
def success(username, current_count):
    """Prints a success message and saves the username to the file."""
    # The 'current_count' is passed in to ensure the printout is accurate
    print(f"{bcolors.OKBLUE}[{current_count}/{NAMES}] [+] Found Username: {username}{bcolors.ENDC}")
    with open(FILE, 'a+') as f:
        f.write(f"{username}\n")

def failure(username, message):
    """Prints a failure message with the reason from the API."""
    # In non-debug mode, we might not want to see every failure.
    # To keep the output clean, let's only print failures in DEBUG mode.
    if DEBUG:
        print(f'{bcolors.FAIL}[-] {username} is invalid/taken. Reason: {message}{bcolors.ENDC}')

def make_numeric_username(length):
    """Generates a random username consisting only of digits."""
    digits = string.digits
    return ''.join(random.choice(digits) for _ in range(length))

def check_username_api(username):
    """
    Checks a username against the Roblox API.
    Returns the JSON response or None on error.
    """
    url = f'https://auth.roblox.com/v1/usernames/validate?request.username={username}&request.birthday={BIRTHDAY}'
    try:
        if DEBUG:
            print(f"{bcolors.GRAY}[DEBUG] Requesting URL: {url}{bcolors.ENDC}")
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if DEBUG:
            print(f"{bcolors.WARNING}[!] Network error for {username}: {e}{bcolors.ENDC}")
        return None # Indicate an error occurred

def worker():
    """The function each thread will execute."""
    global found_count
    
    while True:
        # Check if we've already found enough names before grabbing a new task
        if found_count >= NAMES:
            break

        try:
            # Get a username from the queue. Blocks for 1 sec then times out.
            username = task_queue.get(timeout=1)
        except queue.Empty:
            # If the queue is empty and we're still running, just continue
            continue

        result = check_username_api(username)

        if result: # If the request was successful
            if DEBUG:
                print(f"{bcolors.GRAY}[DEBUG] API Response for {username}: {result}{bcolors.ENDC}")

            code = result.get('code')
            message = result.get('message')

            if code == 0:
                # Use a lock to safely update the shared counter and write to the file
                with found_lock:
                    # Double-check inside the lock to avoid extra writes if another thread just hit the goal
                    if found_count < NAMES:
                        found_count += 1
                        success(username, found_count)
            else:
                failure(username, message)
        
        task_queue.task_done()

# --- Main Execution ---
if __name__ == "__main__":
    print(f"{bcolors.HEADER}--- Roblox Numeric Username Checker (Threaded) ---{bcolors.ENDC}")
    print(f"Seeking {NAMES} usernames of length {LENGTH} using {NUM_THREADS} threads.")
    if DEBUG:
        print(f"{bcolors.WARNING}DEBUG mode is ON. Expect verbose output.{bcolors.ENDC}")

    # Create and start the worker threads
    threads = []
    for _ in range(NUM_THREADS):
        thread = threading.Thread(target=worker, daemon=True) # Daemon threads exit when main program exits
        thread.start()
        threads.append(thread)

    # Main thread's job: fill the queue with tasks
    try:
        while found_count < NAMES:
            # Keep the queue from getting excessively large
            if task_queue.qsize() < NUM_THREADS * 5:
                username = make_numeric_username(LENGTH)
                task_queue.put(username)
            time.sleep(0.01) # Small sleep to prevent this loop from hogging CPU
    except KeyboardInterrupt:
        print(f"\n{bcolors.WARNING}Script interrupted by user. Shutting down...{bcolors.ENDC}")
        # Set found_count to NAMES to signal threads to stop
        found_count = NAMES
    
    print(f"\n{bcolors.OKBLUE}[!] Goal reached. Waiting for all tasks to complete...{bcolors.ENDC}")
    
    # Wait for the queue to be empty
    task_queue.join()

    print(f"{bcolors.OKBLUE}[!] Finished. Found {found_count} usernames.{bcolors.ENDC}")
