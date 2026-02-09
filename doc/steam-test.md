# Testing steam app id extraction

```
➜  ./kdotest.sh
 Window ID: {c4b06b23-feff-42ce-a20e-1c8c9d832a20}
  Name: 
  Class: plasmashell
  PID: 3491

 Window ID: {2f41f541-ea9d-4220-9284-8fed292f2d8c}
  Name: 
  Class: plasmashell
  PID: 3491

 Window ID: {e408e8d6-26ad-4b70-8e25-ab5589397975}
  Name: Wayland to X Recording bridge — Xwayland Video Bridge
  Class: xwaylandvideobridge
  PID: 3927

*Window ID: {ebee0b3e-c344-4e78-afb7-3b4485c2aba2}
  Name: ./kdotest.sh
  Class: org.gnome.Ptyxis
  PID: 4793

 Window ID: {e6627878-108b-4682-8633-839ddca687ac}
  Name: KWin scripting API | Developer - Google Chrome
  Class: google-chrome
  PID: 9078

 Window ID: {37d0296c-5727-4005-a7b7-d12051b244bf}
  Name: PR proposed, feedback/interest from devs? "Autopages" · Issue #548 · StreamController/StreamController - Google Chrome
  Class: google-chrome
  PID: 9078

 Window ID: {6a60de18-6a20-47c7-8be2-3480460ff204}
  Name: KDE.py - StreamController [Dev Container: StreamController Development @ unix:///run/user/1000/podman/podman.sock] - Visual Studio Code
  Class: code
  PID: 223546

 Window ID: {49520fa2-a150-40fa-8b3b-efe75bf85c06}
  Name: Welcome - Visual Studio Code
  Class: code
  PID: 223546

 Window ID: {feaef22b-7952-4043-931a-596ed57fd30d}
  Name: Google Gemini
  Class: chrome-edgehdhbjaibhjojegjhbanemfpnkjkh-Default
  PID: 9078

 Window ID: {4f401fb9-c942-4540-9bc1-b847370e9c8b}
  Name: Google Drive - My Drive - Google Drive
  Class: chrome-aghbiahbpaijignceidepookljebhfak-Default
  PID: 9078

 Window ID: {dcfc433e-0507-4fcf-9f6b-5dec7ef78b0f}
  Name: #app-feature-ideas | StreamController - Discord
  Class: discord
  PID: 352116

 Window ID: {8625a744-d57a-42c1-ba82-87fad22a462b}
  Name: kdotest.sh - autopage - Visual Studio Code
  Class: code
  PID: 223546

 Window ID: {7b428cef-1598-42e6-9f05-48271a763fbf}
  Name: Steam
  Class: steam
  PID: 395181

 Window ID: {b2306a14-aa64-4ff1-bf2d-3212b002420f}
  Name: Oxygen Not Included
  Class: OxygenNotIncluded
  PID: 398293
```


```
sudo cat /proc/398293/environ | tr '\0' '\n' | grep SteamAppId
SteamAppId=457140
```
