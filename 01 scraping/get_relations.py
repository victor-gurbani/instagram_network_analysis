import instaloader
import time
import sys
from alive_progress import alive_bar
import copy
import json

print("Starting") 
with open('../config.json') as config_file:
  config = json.load(config_file)
  username = config['username']

L = instaloader.Instaloader()
L.load_session_from_file(username)
relations_file = 'relations.txt'
my_followers = []
my_followers_left = []

with open('my_followers.txt') as f:
    my_followers = [line.strip() for line in f.readlines()]

with open('my_followers_left.txt') as f:
    my_followers_left = [line.strip() for line in f.readlines()]

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
        print('sed -i "" -e "1d" my_followers_left.txt')
        print("Exit now if necessary\r", end="")
        time.sleep(10)

except Exception as e:
  print(f"Error: {e}")
  print("Error") 

          
print("Done")
