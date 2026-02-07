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

# Discuss

For more details/discussion see this [issue](https://github.com/StreamController/StreamController/issues/548)
