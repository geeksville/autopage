# Autopage

A way to **easily** automatically have pages/button behaviors without having to manually populate each page/button via the [StreamController](https://streamcontroller.github.io/docs/latest/) GUI.

Users can write a small text file to support a new app with keybindings/buttons that will automatically be added to the streamdeck when that app is in the foreground.

These application recipes are sharable (so we can build a library of auto-configured apps). By default, Autopage automatically imports 'approved' contributions from [autopage-recipes](https://github.com/geeksville/autopage-recipes). If you add new apps, please send in a pull request!

# Features

* Default mode: Just blindly installs auto-generated pages onto your StreamControllers. This works fine while the number of app recipes is still small.
* Background mode: Stays running watching your StreamController, only adds pages if and when it sees a supported app being run on your machine. Eventually, if/when there are many app recipes, this will become the default mode of operation.
* Easy! A variety of applications are automatically supported, but if one is missing you can [add it](https://github.com/geeksville/autopage-recipes?tab=readme-ov-file#a-minimal-app-definition).

Here's a short [video](https://youtu.be/nWYgs0SE4BA) demonstrating usage.

## Installation

* Install the "OS" plug-in from the StreamController store. This is needed to let the "typing" actions type keys.
* Install "Material design icon pack" from the store, because the buttons will look **better** with icons. (Autopage works with all icon packs, but this is a good default one to use)
* Install [pipx](https://pipx.pypa.io/stable/installation/) if you don't already have it.
* Run "pipx install stream-autopage"

## Usage

* "autopage" - This will install known autopage definitions onto your StreamController (try this first).
* "autopage --listen" - This will run in the background and only create pages if it sees you use a supported app. (Until there are lots of pages you probably don't need to bother with this)
* "autopage somepath/foo.ap.toml" - Uses just a single ap.toml file (for testing/using your own new app definitions).

# A note to StreamController developers

* I've structured this app so that someday we could just move it into the StreamController flatpak. When that happens, I'm happy to move this repo (and the recipes repo) to your organization. Mostly I just want it to be useful. ;-)

## History

* (DONE) Release 0.1: Implement example foo.ap.toml files for: vscode, kate editor, ptyxis shell. Mostly to make sure basic operation works and the toml syntax is brief but clear/simple. This first version blindly creates pages (via api_client) 1:1 for any found ap.toml files and then exits.
* (DONE) Release 0.2: Subscribes to foregroundWindowName/Class notifications, and only creates autopage pages for apps the user actually encounters on their machine. Remains running as a daemon and when it is notified of the current app changes, creates and activates a new page as needed.
* (SOMEDAY) Release 0.3: Use the Steam APIs to auto-detect running Steam games and automatically create template ap.toml files for any encountered games, set the background image for that page based on Steam store image.

# Streamclient

This project also contains a small command-line client for the StreamController app. I needed it for testing the app API, but eventually it might be useful for others:

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
