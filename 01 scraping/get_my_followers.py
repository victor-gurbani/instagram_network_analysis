import json
# Get instance
import instaloader
L = instaloader.Instaloader()

# Login or load session
with open('../config.json') as config_file:
  config = json.load(config_file)
  username = config['username']

L = instaloader.Instaloader()
L.load_session_from_file(username)

# Obtain profile metadata
profile = instaloader.Profile.from_username(L.context, username)

# Print list of followees
follow_list = []
count=0
for followee in profile.get_followers():
    follow_list.append(followee.username)
    file = open("followers.txt","a+")
    file.write(follow_list[count])
    file.write("\n")
    file.close()
    print(follow_list[count])
    count=count+1
