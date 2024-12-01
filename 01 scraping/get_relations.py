import instaloader
import time
import sys
#from alive_progress import alive_bar
import copy
import json
import os
import platform

print("Starting") 

with open('../config.json') as config_file:
  config = json.load(config_file)
  username = config['username']

L = instaloader.Instaloader()
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
    with open('my_followers_left.txt', 'w') as f:
        for follower in my_followers:
            f.write(f"{follower}\n")
    my_followers_left = my_followers.copy()
  
try:
  with open(relations_file, 'a') as f:
    for follower in my_followers_left:
        print(f"Getting relations for {follower}")

        profile = instaloader.Profile.from_username(L.context, follower)
        tempFollowees = profile.get_followees()
        #tempFollowees2 = copy.deepcopy(tempFollowees)
        #howMany = sum(1 for _ in tempFollowees2)
        print("Saved followees.", end="")
        time.sleep(0.5)
        print("\rProcessing followees...\r", end="")
        countMutual = 0
        #with alive_bar(howMany) as bar:
        for followee in tempFollowees:
          time.sleep(0.05)
          #print(followee)
          #print(followee.username)
          if followee.username.strip() in my_followers:
            #print(f"{follower} {followee.username}\n")
            f.write(f"{follower} {followee.username}\n")
            f.flush()
            countMutual = countMutual + 1
          #bar()
          
        print("Mutual: ", countMutual, " followees")
        if countMutual == 0:
            sys.exit()

        if platform.system() == 'Windows':
            with open('my_followers_left.txt', 'r') as f:
                lines = f.readlines()
            with open('my_followers_left.txt', 'w') as f:
                f.writelines(lines[1:])
        else:
            os.system('sed -i "" -e "1d" my_followers_left.txt')
        
        print("Exit now if necessary\r", end="")
        time.sleep(10)

except Exception as e:
  print(f"Error: {e}")
  print("Error") 

          
print("Done")
