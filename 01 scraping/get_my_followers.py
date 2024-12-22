import json
from time import sleep
import instaloader

# Get instance
with open('../config.json') as config_file:
  config = json.load(config_file)
  username = config['username']
  user_agent = config.get('user_agent', None)

L = instaloader.Instaloader(user_agent=user_agent)

# Login or load session
L.load_session_from_file(username)

# Obtain profile metadata
profile = instaloader.Profile.from_username(L.context, username)

# Print list of followers
followers_list = []
count = 0
for follower in profile.get_followers():
  sleep(0.1)
  followers_list.append(follower.username)
  with open("followers.txt", "a+") as file:
    file.write(followers_list[count])
    file.write("\n")
  print(followers_list[count])
  count += 1

# Print list of followees
followees_list = []
count = 0
for followee in profile.get_followees():
  sleep(0.1)
  followees_list.append(followee.username)
  with open("followees.txt", "a+") as file:
    file.write(followees_list[count])
    file.write("\n")
  print(followees_list[count])
  count += 1
