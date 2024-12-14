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

# Print list of followees
follow_list = []
count = 0
for followee in profile.get_followers():
  sleep(0.1)
  follow_list.append(followee.username)
  with open("followers.txt", "a+") as file:
    file.write(follow_list[count])
    file.write("\n")
  print(follow_list[count])
  count += 1
