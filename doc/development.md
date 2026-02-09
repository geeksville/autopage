# Developers guide

Not currently ready, for now here's my original notes:

## Mini-spec

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