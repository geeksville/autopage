# A sample log of installing autopage and streamclient

```bash
StreamController git:(pr-api) pipx install stream-autopage   
  installed package stream-autopage 0.2.1, installed using Python 3.12.3
  These apps are now globally available
    - autopage
    - streamclient
done! ✨ 🌟 ✨
➜  StreamController git:(pr-api) streamclient
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
➜  StreamController git:(pr-api) streamclient pages
Development
Test1
➜  StreamController git:(pr-api) autopage 
INFO: Discovering repos from https://raw.githubusercontent.com/geeksville/autopage-recipes/refs/heads/main (dev=False)
INFO: Found 5 repo(s) of kind 'ap'
INFO: Connecting to the session bus.
INFO: Connecting to the session bus.
INFO: Known pages on controller: {'Test1', 'Development'}
INFO: Processing repo 1/5: https://raw.githubusercontent.com/geeksville/autopage-recipes/refs/heads/main/app/code.ap.toml
INFO: Building page from repo config: https://raw.githubusercontent.com/geeksville/autopage-recipes/refs/heads/main/app/code.ap.toml
INFO: Icon catalog: 14658 icon(s) across 3 pack(s)
INFO: Resolved icon 'fullscreen' → data/icons/com_core447_MaterialIcons/icons/fullscreen.png
INFO: Resolved icon 'content_copy' → data/icons/com_core447_MaterialIcons/icons/content_copy.png
INFO: Resolved icon 'content_cut' → data/icons/com_core447_MaterialIcons/icons/content_cut.png
INFO: Resolved icon 'content_paste' → data/icons/com_core447_MaterialIcons/icons/content_paste.png
INFO: Resolved icon 'code' → data/icons/com_core447_MaterialIcons/icons/code.png
INFO: Resolved icon 'terminal' → data/icons/com_core447_MaterialIcons/icons/terminal.png
INFO: Resolved icon 'start' → data/icons/com_core447_MaterialIcons/icons/start.png
INFO: Resolved icon 'pause' → data/icons/com_core447_MaterialIcons/icons/pause.png
INFO: Resolved icon 'arrow_forward' → data/icons/com_core447_MaterialIcons/icons/arrow_forward.png
INFO: Resolved icon 'arrow_downward' → data/icons/com_core447_MaterialIcons/icons/arrow_downward.png
INFO: Resolved icon 'arrow_upward' → data/icons/com_core447_MaterialIcons/icons/arrow_upward.png
INFO: Resolved icon 'replay' → data/icons/com_core447_MaterialIcons/icons/replay.png
INFO: Resolved icon 'stop' → data/icons/com_core447_MaterialIcons/icons/stop.png
INFO: Found 2 controller(s): ['A00SA5282I2LRM', 'fake-deck-1']
INFO: Generated page 'code' with 13 button(s)
INFO: Page 'code' pushed to StreamController
INFO: Processing repo 2/5: https://raw.githubusercontent.com/geeksville/autopage-recipes/refs/heads/main/app/ptyxis.ap.toml
INFO: Building page from repo config: https://raw.githubusercontent.com/geeksville/autopage-recipes/refs/heads/main/app/ptyxis.ap.toml
INFO: Icon catalog: 14658 icon(s) across 3 pack(s)
INFO: Resolved icon 'fullscreen' → data/icons/com_core447_MaterialIcons/icons/fullscreen.png
INFO: Resolved icon 'content_copy' → data/icons/com_core447_MaterialIcons/icons/content_copy.png
INFO: Resolved icon 'content_cut' → data/icons/com_core447_MaterialIcons/icons/content_cut.png
INFO: Resolved icon 'content_paste' → data/icons/com_core447_MaterialIcons/icons/content_paste.png
INFO: Resolved icon 'add_to_photos' → data/icons/com_core447_MaterialIcons/icons/add_to_photos.png
INFO: Resolved icon 'arrow_back' → data/icons/com_core447_MaterialIcons/icons/arrow_back.png
INFO: Resolved icon 'arrow_forward' → data/icons/com_core447_MaterialIcons/icons/arrow_forward.png
INFO: Resolved icon 'stop' → data/icons/com_core447_MaterialIcons/icons/stop.png
INFO: Found 2 controller(s): ['A00SA5282I2LRM', 'fake-deck-1']
INFO: Generated page 'ptyxis' with 8 button(s)
INFO: Page 'ptyxis' pushed to StreamController
INFO: Processing repo 3/5: https://raw.githubusercontent.com/geeksville/autopage-recipes/refs/heads/main/app/dolphin.ap.toml
INFO: Building page from repo config: https://raw.githubusercontent.com/geeksville/autopage-recipes/refs/heads/main/app/dolphin.ap.toml
INFO: Icon catalog: 14658 icon(s) across 3 pack(s)
INFO: Resolved icon 'content_copy' → data/icons/com_core447_MaterialIcons/icons/content_copy.png
INFO: Resolved icon 'content_cut' → data/icons/com_core447_MaterialIcons/icons/content_cut.png
INFO: Resolved icon 'content_paste' → data/icons/com_core447_MaterialIcons/icons/content_paste.png
INFO: Resolved icon 'place' → data/icons/com_core447_MaterialIcons/icons/place.png
INFO: Resolved icon 'terminal' → data/icons/com_core447_MaterialIcons/icons/terminal.png
INFO: Resolved icon 'info' → data/icons/com_core447_MaterialIcons/icons/info.png
INFO: Resolved icon 'folder' → data/icons/com_core447_MaterialIcons/icons/folder.png
INFO: Resolved icon 'home' → data/icons/com_core447_MaterialIcons/icons/home.png
INFO: Resolved icon 'arrow_upward' → data/icons/com_core447_MaterialIcons/icons/arrow_upward.png
INFO: Found 2 controller(s): ['A00SA5282I2LRM', 'fake-deck-1']
INFO: Generated page 'dolphin' with 9 button(s)
INFO: Page 'dolphin' pushed to StreamController
INFO: Processing repo 4/5: https://raw.githubusercontent.com/geeksville/autopage-recipes/refs/heads/main/app/chrome.ap.toml
INFO: Building page from repo config: https://raw.githubusercontent.com/geeksville/autopage-recipes/refs/heads/main/app/chrome.ap.toml
INFO: Icon catalog: 14658 icon(s) across 3 pack(s)
INFO: Resolved icon 'content_copy' → data/icons/com_core447_MaterialIcons/icons/content_copy.png
INFO: Resolved icon 'content_cut' → data/icons/com_core447_MaterialIcons/icons/content_cut.png
INFO: Resolved icon 'content_paste' → data/icons/com_core447_MaterialIcons/icons/content_paste.png
INFO: Resolved icon 'home' → data/icons/com_core447_MaterialIcons/icons/home.png
INFO: Resolved icon 'tab' → data/icons/com_core447_MaterialIcons/icons/tab.png
INFO: Resolved icon 'open_in_new' → data/icons/com_core447_MaterialIcons/icons/open_in_new.png
INFO: Resolved icon 'visibility_off' → data/icons/com_core447_MaterialIcons/icons/visibility_off.png
INFO: Resolved icon 'arrow_back' → data/icons/com_core447_MaterialIcons/icons/arrow_back.png
INFO: Resolved icon 'arrow_forward' → data/icons/com_core447_MaterialIcons/icons/arrow_forward.png
INFO: Resolved icon 'zoom_in' → data/icons/com_core447_MaterialIcons/icons/zoom_in.png
INFO: Resolved icon 'zoom_out' → data/icons/com_core447_MaterialIcons/icons/zoom_out.png
INFO: Found 2 controller(s): ['A00SA5282I2LRM', 'fake-deck-1']
INFO: Generated page 'chrome' with 11 button(s)
INFO: Page 'chrome' pushed to StreamController
INFO: Processing repo 5/5: https://raw.githubusercontent.com/geeksville/autopage-recipes/refs/heads/main/game/oni.ap.toml
INFO: Building page from repo config: https://raw.githubusercontent.com/geeksville/autopage-recipes/refs/heads/main/game/oni.ap.toml
INFO: Icon catalog: 14658 icon(s) across 3 pack(s)
INFO: Resolved icon 'fullscreen' → data/icons/com_core447_MaterialIcons/icons/fullscreen.png
INFO: Resolved icon 'content_copy' → data/icons/com_core447_MaterialIcons/icons/content_copy.png
INFO: Resolved icon 'construction' → data/icons/com_core447_MaterialIcons/icons/construction.png
INFO: Resolved icon 'cleaning_services' → data/icons/com_core447_MaterialIcons/icons/cleaning_services.png
INFO: Resolved icon 'clear' → data/icons/com_core447_MaterialIcons/icons/clear.png
INFO: Resolved icon 'speed' → data/icons/com_core447_MaterialIcons/icons/speed.png
INFO: Resolved icon 'home' → data/icons/com_core447_MaterialIcons/icons/home.png
INFO: Resolved icon 'pause' → data/icons/com_core447_MaterialIcons/icons/pause.png
INFO: Found 2 controller(s): ['A00SA5282I2LRM', 'fake-deck-1']
INFO: Generated page 'oni' with 8 button(s)
INFO: Page 'oni' pushed to StreamController
➜  StreamController git:(pr-api) 
```