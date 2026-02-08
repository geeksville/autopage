# Changes needed in StreamController

## Near term todo

* check for and replace existing screen names
* make button coordinates optional
* use toml-repos to support matching multiple files
* support special keys like F13 or COPY or PASTE
* remove dbus-python==1.3.2 dependency from streamcontroller - use dasbus instead

## Eventually (not now)

* let user use standard color names instead of hex constants
* send background images to controller
* make api notify-foreground work like kdotool
* make api property notifications work for page change
* publish pipx app
* package pipx app as a homebrew app (with homebrew-release-action - which will publish to my 'tap')
