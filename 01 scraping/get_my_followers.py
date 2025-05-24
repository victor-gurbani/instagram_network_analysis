from time import sleep
import instaloader # Still needed for Profile.from_username
from .insta_utils import init_instaloader # Relative import

def fetch_followers_followees():
    L_instance, session_username = init_instaloader()

    if not L_instance or not session_username:
        print("Failed to initialize Instaloader. Exiting.")
        return

    try:
        # Obtain profile metadata
        profile = instaloader.Profile.from_username(L_instance.context, session_username)
        print(f"Fetching followers and followees for {session_username}...")

        # Print list of followers
        followers_list = []
        print("\nFollowers:")
        with open("followers.txt", "w") as file: # Overwrite file each run
            for i, follower in enumerate(profile.get_followers()):
                sleep(0.1) # Be respectful to Instagram's rate limits
                followers_list.append(follower.username)
                file.write(follower.username + "\n")
                print(f"{i+1}. {follower.username}")
        print(f"Total followers: {len(followers_list)}")

        # Print list of followees
        followees_list = []
        print("\nFollowees:")
        with open("followees.txt", "w") as file: # Overwrite file each run
            for i, followee in enumerate(profile.get_followees()):
                sleep(0.1) # Be respectful to Instagram's rate limits
                followees_list.append(followee.username)
                file.write(followee.username + "\n")
                print(f"{i+1}. {followee.username}")
        print(f"Total followees: {len(followees_list)}")

    except instaloader.exceptions.ProfileNotExistsException:
        print(f"Profile {session_username} not found.")
    except instaloader.exceptions.ConnectionException as e:
        print(f"Connection error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == '__main__':
    fetch_followers_followees()
