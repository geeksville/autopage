# Autopage

An easy way to textually describe (on a per app basis) easy automatic keybindings/buttons that will be added to the streamdeck when that app is in the foreground.  

WARNING You probably don't want this yet - I'm still writing it.

# Mini-spec

A way to **easily** automatically have pages/button behaviors without having to manually populate each page/button via the GUI. 

* Get informed by streamcontroller when the foreground app changes. 
* Based on window class/name regexes try to find a foo.ap.toml file for that app.  If found, parse that file and add buttons/actions.
* Autopage defs can be bunded into the app or in a [toml-repo](https://pypi.org/project/toml-repo/).  I'll create semi public 'master' autopages repo which anyone can send in PRs to to add new apps.  If you'd like we can someday move it into your StreamController gh org?
* I'll premake and include a set of common autopage def files (kwrite, vscode, etc..)
* Whenever the foreground app changes, if the user hasn't already specified a page for that app and and a ab.toml match is found -> create a page for that user.  Icons and labels will be auto selected for buttons based on regex matching vs the users installed asset packs.

This TBD foo.ap.toml file will say stuff like:

*  "I'm for kwrite or vscode or gimp"
* Here's a list of buttons node (this node can have stuff like background color specified if the user wishes)
* Add a button with icon "copy" whos action is "paste ctrl-c"  (it will search <icon pack> for icons matching that regex). 
* Alternate more flexible ways of specifying custom icons could be provided in the future)
(The format will be very human readable and succinct - but it will be processed to generate json compatible with your existing import/export page format)

## App Ids

Also the same app-id -> autobutton defs lookup scheme could be used to let users define standard mappings for Steam games.  I'm thinking the resolution would work based on a few types of expressions:

* flatpak://foo.blah.app
* steam://store/{appid}/
* regex://?class=classnamestr&name=somewinnameregex (ex: "class=org.gnome.Ptyxis" or "class=code" name=".*foo.*" which admittedly is somewhat weak as a 'unique' identifier but it is easy and easy for users to understand)

## Usage

* autopage somepath/foo.ap.toml - Uses just a single ap.toml file (for testing)
* autopage http://someurl/foo - Looks for an ap.toml file in that URL (using toml-repo), this will implicitly load many possible ap definition files


Uses streamcontroller ali_client.AddPage() to add/remove pages as needed.  

* (CURRENT) Release 0.1: Implement example foo.ab.toml files for: vscode, kate editor, ptyxis shell.  Mostly to make sure basic operation works and the toml syntax is brief but clear/simple.  This first version blindly creates pages (via api_client) 1:1 for any found ab.toml files and then exits.
* (SOMEDAY) Release 0.2: Subscribes to foregroundWindowName/Class notifications, and only creates autobutton pages for apps the user actually encounters on their machine.  Remains running as a daemon and when it is notified of the current app changes, creates and activates a new page as needed.
* (SOMEDAY) Release 0.3: Use the steam APIs to auto detect running steam games and automatically create template ab.toml files for any encountered games, set the background image for that page based on Steam store image

* Use my toml-repo package to autofetch foo.ab.toml files from a git repo (that others can contribute to). 

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
