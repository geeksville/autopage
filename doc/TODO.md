# Changes needed in StreamController

## Near term todo

* !get kdotool working
* put the uscrs in a special directory so next/prev doesn't select them
* if there is no match when doing --listen, switch to the default uscr
* support wildcard matching for icon names by looking at icon_dir like in https://github.com/stylesuxx/python-material-icons/blob/master/examples/pygame-gallery.py

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
