import sys
import os
import json # For potential JSONDecodeError
from instaloader import Instaloader, exceptions as instaloader_exceptions

# Add the '03 analysis' directory to sys.path to allow importing helper_functions
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '03 analysis')))
from helper_functions import load_config, get_username_from_config

def init_instaloader():
    """
    Initializes Instaloader with configuration from ../config.json.
    Loads the session for the configured username.

    Returns:
        tuple: (Instaloader_instance, username) or (None, None) if initialization fails.
    """
    config = load_config()
    if not config:
        print("Error: Could not load config.json. Instaloader initialization failed.")
        return None, None

    username = config.get('username')
    user_agent = config.get('user_agent')

    if not username:
        print("Error: 'username' not found in config. Instaloader initialization failed.")
        return None, None
    
    # user_agent is optional for Instaloader, but good practice to set if available
    if user_agent:
        L = Instaloader(user_agent=user_agent)
    else:
        L = Instaloader()
        print("Warning: 'user_agent' not found in config. Proceeding without it.")

    try:
        print(f"Attempting to load session for username: {username}")
        L.load_session_from_file(username)
        print(f"Session loaded successfully for {username}.")
        return L, username
    except FileNotFoundError:
        print(f"Error: Session file for username '{username}' not found.")
        print("Please make sure you have logged in previously using Instaloader,")
        print("or run a script that performs login (e.g., instaloader -l your_username).")
        return None, None
    except instaloader_exceptions.ConnectionException as e:
        print(f"Error loading session for {username}: ConnectionException - {e}")
        print("This might be due to an invalid session file or network issues.")
        return None, None
    except Exception as e: # Catch any other Instaloader specific or general exceptions during session load
        print(f"An unexpected error occurred while loading session for {username}: {e}")
        return None, None

if __name__ == '__main__':
    # Example usage / test
    # Ensure config.json exists at the root with 'username' and optionally 'user_agent'
    # And a session file for the username exists (e.g., after running 'instaloader -l your_username')
    
    # To run this test, you'd need to ensure config.json has a user_agent or modify the test.
    # For now, let's assume config.json might not have user_agent for this direct test.
    # And that a session file for 'testuser' exists.
    
    print("Testing init_instaloader...")
    L_test, username_test = init_instaloader()
    if L_test and username_test:
        print(f"Successfully initialized Instaloader for {username_test}.")
        try:
            profile = Instaloader.Profile.from_username(L_test.context, username_test)
            print(f"Successfully fetched profile for {profile.username} with {profile.followers} followers.")
        except Exception as e:
            print(f"Could not fetch profile after loading session: {e}")
    else:
        print("Failed to initialize Instaloader.")
