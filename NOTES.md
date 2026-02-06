# Misc notes for geeksville

for https://github.com/StreamController/StreamController/issues/548 
* make work with games!
* let AI recommend icons
* optionally let autobutton files say they want a full screen
* let autobutton def files specify a screen background which is used if one is not set - for steam games pull this from steam
* allow multiple autobutton groups to show on same screen? i.e. media controls should be included if space allows
* somehow unify with SteamInput and that new bazzite input mapper project?

## Steam art

Yes, but you don't need a heavy library for it. The "Official Steam API" is overkill (requiring API keys and protobufs) for just fetching a JPEG.

You want the Storefront API, which is public, unauthenticated, and returns JSON.

1. The "No Library" Way (Best Practice)
The library that "abstracts" this is just requests. Installing a dedicated Steam library just to parse one JSON field is like buying a semi-truck to carry a single grocery bag.

Here is the Python snippet to get the Store Page Background:

Python
import requests

def get_steam_background(app_id):
    url = "https://store.steampowered.com/api/appdetails"
    params = {"appids": app_id}
    
    response = requests.get(url, params=params)
    data = response.json()
    
    # Validation: Check if the app actually exists and succeeded
    if data[str(app_id)]["success"]:
        return data[str(app_id)]["data"]["background"]
    else:
        return None

# Example: Oxygen Not Included
print(get_steam_background(457140))
2. The "CDN Hack" Way (Faster)
If you don't want to wait for a JSON response and just want to guess the URL (which works 99% of the time), you can hit Valve's CDN directly.

Store Background: https://cdn.akamai.steamstatic.com/steam/apps/{app_id}/page_bg_generated_v6b.jpg

Library Hero (The wide banner): https://cdn.akamai.steamstatic.com/steam/apps/{app_id}/library_hero.jpg

Library Logo: https://cdn.akamai.steamstatic.com/steam/apps/{app_id}/logo.png

3. The "I Want Good Art" Way
The default Steam backgrounds are often dark, cluttered, or just screenshots.

If you are building a dashboard (like for your StreamController), you actually want SteamGridDB. They have a Python library that fetches curated, high-res artwork that doesn't look like a Geocities page.

Bash
pip install steamgrid-db
Python
from steamgrid import SteamGridDB

sgdb = SteamGridDB('YOUR_API_KEY')
grid = sgdb.get_grids_by_id(457140) # ONI
print(grid[0].url)
Recommendation: Start with the CDN Hack (Method 2). It requires zero code logic, just string interpolation. If that 404s, fall back to the JSON API.