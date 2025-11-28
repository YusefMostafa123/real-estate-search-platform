from pathlib import Path
import os

# Constants for later use
MILES_PER_DEG = 69.0
RADIUS_MILES = 0.6
MILES_PER_DEGREE = 69.0
RADIUS_DEG = RADIUS_MILES / MILES_PER_DEGREE
RADIUS_SQ = RADIUS_DEG * RADIUS_DEG
LOW_MAX_CRIMES = 166
MEDIUM_MAX_CRIMES = 625
ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "home_explorer.db"
PORT = 5001
TEMPLATE_PATH = f'{ROOT}/templates'
STATIC_PATH = f'{ROOT}/static'

# Given: # of Total Crimes
# Returns: String of relative crime rate
def crime_severity_label(total_crimes: int) -> str:
    """Map total crimes to Low / Medium / High."""
    if total_crimes <= 166:
        return "Low"
    elif total_crimes <= 625:
        return "Medium"
    else:
        return "High"
    
def print_init_db_message():
    print_line()
    print("IF YOU ARE SEEING THIS, YOU HAVE CHOSEN TO REBOOT THE DATABASE")
    print("THIS IS A LENGTHY PROCESS. PLEASE WAIT PATIENTLY FOR IT TO COMPLETE")
    print("DO NOT CLOSE THE INTURRUPT THIS PROCESS. IT COULD LEAD TO DATA LOSS.")
    print("EVERY TIME YOU CHANGE RUNNER.PY AND SAVE, THIS PROCESS WILL BEGIN AGAIN.")
    print_line()

def print_welcome_message():
    print_line()
    print("Welcome to the Home Listing and Price Explorer!")
    print_line()
    print(f"Running on http://127.0.0.1:{PORT}")
    print("Press CTRL + C in the terminal to close this application")


def clear_terminal():
    # For Windows
    if os.name == 'nt':
        _ = os.system('cls')
    # For Mac and Linux (POSIX systems)
    else:
        _ = os.system('clear')

def print_line(): 
    print("*******************************")