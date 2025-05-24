import instaloader
import time
import sys
import copy
import json
import os
import platform
import argparse
from insta_utils import init_instaloader # Absolute import

print("Starting")

# Initialize Instaloader and load session
L_instance, logged_in_username = init_instaloader()

if not L_instance or not logged_in_username:
    print("Failed to initialize Instaloader. Exiting.")
    sys.exit(1)

# Parse command-line arguments
parser = argparse.ArgumentParser(description='Get relations of a target Instagram profile.')
parser.add_argument('--username', type=str, default=None, help='Target username to get relations for (defaults to username in config.json)')
parser.add_argument('--wait-time', type=int, default=10, help='Time to wait between processing people, in seconds (default: 10)')
parser.add_argument('--max-count', type=int, default=-1, help='Maximum number of followers to process before exiting (default: -1 for no limit)')
parser.add_argument('--no-animation', action='store_true', help='Disable loading animation')
parser.add_argument('--store-data', action='store_true', help='Store detailed follower data in the followers_data directory for future use')
args = parser.parse_args()

target_username = args.username
wait_time = args.wait_time
max_count = args.max_count
no_animation = args.no_animation
store_data = args.store_data

# If target_username is not provided via args, load it from config.json
if not target_username:
    with open('../config.json') as config_file:
        config = json.load(config_file)
        target_username = config.get('username') # This is the target profile
    if not target_username:
        print("Error: Target username not provided in args or found in config.json. Exiting.")
        sys.exit(1)

print(f"Target profile for scraping relations: {target_username}")
print(f"Session loaded for user: {logged_in_username}")


# Create followers_data directory if --store-data is enabled and directory doesn't exist
if store_data and not os.path.exists('followers_data'):
    os.makedirs('followers_data')

relations_file = 'relations.txt'
my_followers = []
my_followers_left = []

try:
    with open('followers.txt') as f:
        my_followers = [line.strip() for line in f.readlines()]
except FileNotFoundError:
    print("followers.txt not found. Please make sure the file exists.")

try:
    with open('my_followers_left.txt') as f:
        my_followers_left = [line.strip() for line in f.readlines()]
except FileNotFoundError:
    print("my_followers_left.txt not found. Creating a new file.")
    my_followers_left = my_followers.copy()  # Create a proper copy in memory first
    
    with open('my_followers_left.txt', 'w') as f:
        for follower_in_list in my_followers_left: # Renamed to avoid conflict
            f.write(f"{follower_in_list}\n")

if not my_followers_left:
    print("Warning: 'my_followers_left.txt' is empty. Rebuilding from 'followers.txt'. It is possible the process has already finished.")
    response = input("Do you want to rebuild 'my_followers_left.txt' from 'followers.txt'? (y/N): ").strip().lower()
    if response == 'y':
        with open('my_followers_left.txt', 'w') as f:
            for follower_in_list in my_followers: # Renamed to avoid conflict
                f.write(f"{follower_in_list}\n")
        my_followers_left = my_followers.copy()
    else:
        print("Skipping rebuild of 'my_followers_left.txt'.")

try:
    with open(relations_file, 'a') as f_relations: # Renamed file handle
        for current_follower_to_process in my_followers_left: # Renamed loop variable
            print(f"Getting relations for {current_follower_to_process}")

            profile = instaloader.Profile.from_username(L_instance.context, current_follower_to_process) # Use L_instance
            tempFollowees = profile.get_followees()
            print("Saved followees.", end="")
            time.sleep(0.5)
            print("\rProcessing followees", end="")

            animation = [' |', ' /', ' -', ' \\']
            anim_index = 0
            countMutual = 0
            
            # Create a file for storing detailed data if --store-data is enabled
            followee_data_file = None
            if store_data:
                followee_data_path = f"followers_data/{profile.username}.{profile.userid}.txt"
                followee_data_file = open(followee_data_path, 'w')
            
            for followee_profile in tempFollowees: # Renamed loop variable
                if not no_animation:
                    print(f"\rProcessing followees{animation[anim_index % len(animation)]}", end="")
                    anim_index += 1
                
                # Store the followee data if --store-data is enabled
                if store_data and followee_data_file:
                    followee_data_file.write(f"{followee_profile.username}\n") # Use followee_profile
                    
                time.sleep(0.05)
                if followee_profile.username.strip() in my_followers: # Use followee_profile
                    f_relations.write(f"{current_follower_to_process} {followee_profile.username}\n") # Use f_relations and updated vars
                    f_relations.flush()
                    countMutual += 1
            
            # Close the data file if it was opened
            if store_data and followee_data_file:
                followee_data_file.close()

            print(" \r", end="")  # Clear the whole line after animation (works even if animation is disabled)

            print("Mutual: ", countMutual, " followees")
            
            #if countMutual == 0:
            #    sys.exit()

            if platform.system() == 'Windows':
                with open('my_followers_left.txt', 'r') as f_r:
                    lines = f_r.readlines()
                with open('my_followers_left.txt', 'w') as f_w:
                    f_w.writelines(lines[1:])
            else:
                os.system('sed -i "" -e "1d" my_followers_left.txt')

            if max_count > 0:
                max_count -= 1
                if max_count == 0:
                    print("Max count reached. Exiting.")
                    break
                
            print("Exit now if necessary\r", end="")
            time.sleep(wait_time)

            

except Exception as e:
    print(f"Error: {e}")
    print("Error")
    sys.exit(1)

with open(relations_file, 'a') as f_relations:
    with open('followers.txt', 'r') as ffol:
            for follower_line in ffol: # Renamed loop variable
                current_follower = follower_line.strip() # Renamed
                if current_follower:
                    # This part writes relations between each follower and the main target_username
                    # This assumes 'username' here should be the target_username from config/args
                    f_relations.write(f"{current_follower} {target_username}\n") # Use f_relations and target_username
                    f_relations.flush()

print("Scraping completed successfully!")
