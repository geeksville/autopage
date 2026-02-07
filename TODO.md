# Changes needed in StreamController

## Near term todo

* create a poetry based project based on the readme, it will be GPLv3 licensed and eventually distributed on pypi
* put the src code in a new module called "autopage" in src/autopage.
* have it import toml-repo from pypi
* include basic empty test framework
* include .github CI actions for publishing to pypi and checking for lint and tests passing
* After this basic build framework is in place stop and let me review

## Eventually (not now)

* make api notify-foreground work like kdotool
* make api property notifications work for page change
* publish pipx app
* package pipx app as a homebrew app (with homebrew-release-action - which will publish to my 'tap')
