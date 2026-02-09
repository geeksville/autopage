# Autopage

A way to **easily** automatically have pages/button behaviors without having to manually populate each page/button via the GUI. 

Users can write a small text file to support a new app with keybindings/buttons that will automatically be added to the streamdeck when that app is in the foreground.  

These application recipes are sharable (so we can build a library of auto configured apps).  By default Autopage automatically imports 'approved' contributions from a [autopage-recipes](https://github.com/geeksville/autopage-recipes).  If you add new apps, please send in a pull request!

# Features

* Default mode: Just blindly installs auto generated pages onto your Streamcontrollers.  This works fine while the number of app recipes is still small.
* Background mode: Stays running watching your Streamcontroller, only adds pages if and when it sees a supported app being run on your machine.  Eventually if/when there are many app recipes this will become the default mode of operation.

## Installation

* Install ""
* Install "Material design icon pack", because the buttons will look better with icons.  (Autopage works with all icon packs, but this is a good default one to use)
* Install [pipx](https://pipx.pypa.io/stable/installation/) if you don't already have it.
* Run "pipx install stream-autopage"

## Usage

* "autopage" - This will install known autopage definitions onto your Streamcontroller (try this first)
* "autopage --listen" - This will run in the background and only create pages if it sees you use a supported app.  (Until there are lots of pages you probably don't need to bother with this)
* "autopage somepath/foo.ap.toml" - Uses just a single ap.toml file (for testing/using your own new app definitions)

# A note to Streamcontroller developers

* I've structured this app so that someday we could just move it into the Streamcontroller flatpak, when that happens I'm happy to move this repo (and the recipes repo to your organization.  Mostly I just want it to be useful. ;-)

## History

* (DONE) Release 0.1: Implement example foo.ab.toml files for: vscode, kate editor, ptyxis shell.  Mostly to make sure basic operation works and the toml syntax is brief but clear/simple.  This first version blindly creates pages (via api_client) 1:1 for any found ab.toml files and then exits.
* (DONE) Release 0.2: Subscribes to foregroundWindowName/Class notifications, and only creates autobutton pages for apps the user actually encounters on their machine.  Remains running as a daemon and when it is notified of the current app changes, creates and activates a new page as needed.
* (SOMEDAY) Release 0.3: Use the steam APIs to auto detect running steam games and automatically create template ab.toml files for any encountered games, set the background image for that page based on Steam store image

# Streamclient

This project also contains a small command line client for the Streamcontroller app.  I needed it for testing the app API but eventually it might be useful for others:

```
> poetry run streamclient
usage: streamclient [-h] {controllers,pages,add-page,remove-page,set-active-page,notify-foreground,icon-packs,icons,get-property,listen} ...

StreamController DBus API client

positional arguments:
  {controllers,pages,add-page,remove-page,set-active-page,notify-foreground,icon-packs,icons,get-property,listen}
    controllers         List connected controller serial numbers
    pages               List all pages
    add-page            Add a new page (based on an optional JSON template)
    remove-page         Remove a page
    set-active-page     Set the active page on a controller
    notify-foreground   Notify foreground window (for testing window title notifications)
    icon-packs          List icon packs
    icons               List icons in a pack
    get-property        Read a DBus property
    listen              Listen for property change notifications

options:
  -h, --help            show this help message and exit
```

# Discuss

For more details/discussion see this [issue](https://github.com/StreamController/StreamController/issues/548)
