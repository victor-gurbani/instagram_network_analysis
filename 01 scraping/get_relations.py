import instaloader
import time
import sys
import copy
import json
import os
import platform
import argparse

print("Starting")

# Parse command-line arguments
parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('--wait-time', type=int, default=10, help='Time to wait between processing people, in seconds (default: 10)')
parser.add_argument('--max-count', type=int, default=-1, help='Maximum number of followers to process before exiting (default: -1 for no limit)')
parser.add_argument('--no-animation', action='store_true', help='Disable loading animation')
args = parser.parse_args()
wait_time = args.wait_time
max_count = args.max_count
no_animation = args.no_animation

with open('../config.json') as config_file:
    config = json.load(config_file)
    username = config['username']
    user_agent = config.get('user_agent', None)

L = instaloader.Instaloader(user_agent=user_agent)
L.load_session_from_file(username)
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
    with open('my_followers_left.txt', 'w') as f:
        for follower in my_followers:
            f.write(f"{follower}\n")
    my_followers_left = my_followers.copy()

if not my_followers_left:
    print("Warning: 'my_followers_left.txt' is empty. Rebuilding from 'followers.txt'. It is possible the process has already finished.")
    response = input("Do you want to rebuild 'my_followers_left.txt' from 'followers.txt'? (y/N): ").strip().lower()
    if response == 'y':
        with open('my_followers_left.txt', 'w') as f:
            for follower in my_followers:
                f.write(f"{follower}\n")
        my_followers_left = my_followers.copy()
    else:
        print("Skipping rebuild of 'my_followers_left.txt'.")

try:
    with open(relations_file, 'a') as f:
        for follower in my_followers_left:
            print(f"Getting relations for {follower}")

            profile = instaloader.Profile.from_username(L.context, follower)
            tempFollowees = profile.get_followees()
            print("Saved followees.", end="")
            time.sleep(0.5)
            print("\rProcessing followees", end="")

            animation = [' |', ' /', ' -', ' \\']
            anim_index = 0
            countMutual = 0
            for followee in tempFollowees:
                if not no_animation:
                    print(f"\rProcessing followees{animation[anim_index % len(animation)]}", end="")
                    anim_index += 1
                time.sleep(0.05)
                if followee.username.strip() in my_followers:
                    f.write(f"{follower} {followee.username}\n")
                    f.flush()
                    countMutual += 1

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

with open(relations_file, 'a') as f:
    with open('followers.txt', 'r') as ffol:
            for line in ffol:
                follower = line.strip()
                if follower:
                    f.write(f"{follower} {username}\n")
                    f.flush()
print("Done")
