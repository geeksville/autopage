# Changes needed in StreamController

## Near term todo

* support default colors
* check for and replace existing screen names
* support window match regexes
* make button coordinates optional
* use toml-repos to support matching multiple files
* let user use standard color names instead of hex constants
* send background images to controller

## Eventually (not now)

* remove dbus-python==1.3.2 dependency from streamcontroller - use dasbus instead
* make api notify-foreground work like kdotool
* make api property notifications work for page change
* publish pipx app
* package pipx app as a homebrew app (with homebrew-release-action - which will publish to my 'tap')
