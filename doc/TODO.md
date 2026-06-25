# Changes needed in StreamController

## Near term todo

* !get kdotool working
* !get background images working
* handle match.steam_app_id for matching a particular window class
* handle background.auto 
* don't auto create all uscrs, only create as needed when detected by --listen
* auto generate toml files for unrecognized apps.  at first, use steam games as the proof of concept
* put the uscrs in a special directory so next/prev doesn't select them
* if there is no match when doing --listen, switch to the default uscr
* currently we apply opacity as part of building the image THAT IS VERY BAD AT RUNTIME, instead just paint the image with a specified opacity at render time
* support wildcard matching for icon names by looking at icon_dir like in https://github.com/stylesuxx/python-material-icons/blob/master/examples/pygame-gallery.py

### steam cover art

Nope. There isn't a magical, all-in-one package that snoops on your active windows and hits up Valve's servers for high-res JPEGs. You're asking for a Frankenstein library that crosses OS-level window management with web API scraping.

But this is Python, so you can easily duct-tape two tools together to do exactly this:

Spot the Game: Use pygetwindow (or win32gui on Windows) to grab the text title of whatever window is currently in the foreground.

Fetch the Data: Feed that window title into a wrapper like python-steam-api to search the Steam store and extract the game's unique AppID.

Once you have the AppID, you don't even need a library to get the art. Steam's content delivery network uses completely predictable URLs. Just plug the ID into this link and grab it with the requests library:

https://steamcdn-a.akamaihd.net/steam/apps/<APP_ID>/library_600x900.jpg
https://steamcdn-a.akamaihd.net/steam/apps/2400160/library_600x900.jpg
https://steamcdn-a.akamaihd.net/steam/apps/2400160/header.jpg  - probably best
https://steamcdn-a.akamaihd.net/steam/apps/2400160/capsule_616x353.jpg 

INFO: Window changed: name='Glyphica' class='steam_app_2400160'

## Old todo

* ask devs about https://github.com/geeksville/StreamController/tree/exp-old-dbus-api
* ask devs about adding api for installing icon packs and plugins
* ask about flatpak being large

## Eventually (not now)

* currently we do button wrapping on the client.  It would be better to have the sc
app have the concept of "nextfreebutton" as a valid position.  look for usages of
key_layout() and add the wrap/cleanup at page load time
* send background images to controller
* publish pipx app
* package pipx app as a homebrew app (with homebrew-release-action - which will publish to my 'tap')
