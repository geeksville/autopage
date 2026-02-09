# Changes needed in StreamController

## Near term todo

* test all shortcuts
* update readme with install instructions
* make a little video
* ask devs about https://github.com/geeksville/StreamController/tree/exp-old-dbus-api
* ask devs about adding api for installing icon packs and plugins

## Eventually (not now)

* currently we do button wrapping on the client.  It would be better to have the sc 
app have the concept of "nextfreebutton" as a valid position.  look for usages of 
key_layout() and add the wrap/cleanup at page load time
* send background images to controller
* publish pipx app
* package pipx app as a homebrew app (with homebrew-release-action - which will publish to my 'tap')
