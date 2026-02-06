#!/bin/bash

# Get all window IDs
window_ids=$(kdotool search .)

# Get the active window ID
active_window=$(kdotool getactivewindow)

# Loop through each window ID
for window_id in $window_ids; do
    # Get window name, class name, and PID
    window_name=$(kdotool getwindowname "$window_id")
    window_class=$(kdotool getwindowclassname "$window_id")
    window_pid=$(kdotool getwindowpid "$window_id")
    
    # Mark active window with an asterisk
    if [ "$window_id" = "$active_window" ]; then
        marker="*"
    else
        marker=" "
    fi
    
    # Print the window ID, name, class name, and PID
    echo "${marker}Window ID: $window_id"
    echo "  Name: $window_name"
    echo "  Class: $window_class"
    echo "  PID: $window_pid"
    echo ""
done
