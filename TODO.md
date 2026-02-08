# Changes needed in StreamController

## Near term todo

* make button coordinates wrap as needed, currently they just fill first row.  look for usages of key_layout() and add the wrap/cleanup at page load time
* use toml-repos to support matching multiple files
* ask devs about https://github.com/geeksville/StreamController/tree/exp-old-dbus-api
* ask devs about adding api for installing icon packs and plugins

## Eventually (not now)

* let user use standard color names instead of hex constants
* send background images to controller
* publish pipx app
* package pipx app as a homebrew app (with homebrew-release-action - which will publish to my 'tap')
