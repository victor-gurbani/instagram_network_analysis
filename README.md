# Instagram Network Analysis (Updated 2024)

**Build an interactive network of your Instagram followers and their relations in 3 easy steps! (and quite some time)**

> [!NOTE]
_Proof of concept. Use at your own responsibility, as it may violate Instagram's TOS._\
_I do not make myself responsible for any consequences to Instagram Accounts after using this project._\
_Instagram might find it suspicious to use bots. To avoid errors, add 2FA and use Instaloader carefully._

## Step 0

Clone the repo:
```bash
git clone https://github.com/victor-gurbani/instagram_network_analysis/
cd instagram_network_analysis 
```
Install the dependencies:
```bash
pip install instaloader -U
pip install requirements.txt
```
And set your Instagram username in the config.json file.
```bash
nano config.json
```

## Step 1

Login to Instagram either using

 1. Instaloader CLI: `instaloader --login=USERNAME`
 2. Your preferred browser and run: `pip install browser-cookie3 -U && instaloader --load-cookies=BROWSER` _where BROWSER is chrome, firefox, safari, etc... To avoid detection, use your browser for a few days._

## Step 2 

Start scraping your profile and your followers followers:
```bash
cd 01\ scraping/
python3 get_my_followers.py
python3 get_relations.py --wait-time 10
python3 relations_to_json.py
```
_--wait-time can be omitted but set it to a high value in seconds to avoid detection. Use --max-count to set a limit on how many users to scrape (progress is saved and can be resumed directly)_

To monitor the scraping you can `tail -F relations.txt `

## Step 3 

Finished! Now **visualise it and process the data!**

Go to the corresponding folder `02 visual` and copy the relations.json file:
```bash
cd 02\ visual/ && cp ../01\ scraping/relations.json relations.json
```
and _start_ or _open_ `index.html` in your preferred browser (with JS enabled).

## Step 4 (optional)

**Analyse the data**

First, go to the third folder copying the data:
```bash
cd 03\ analysis/ && cp ../01\ scraping/relations.* ./
```
And run the analysis scripts! (idk if the community detection works but the other two work fine)

---

Original step-by-step guide on how to use the code and interpret the results: https://medium.com/@maximpiessen/how-i-visualised-my-instagram-network-and-what-i-learned-from-it-d7cc125ef297
