#!/bin/bash

# Wait for Dock to be running
until pgrep -xq "Dock"; do
   sleep 5
done

# Remove all items from Dock
dockutil --remove all --no-restart

# Array of applications to add to the Dock
dockArray=(
	"/System/Applications/Launchpad.app"
	"/System/Applications/Mission Control.app"
	"/Applications/Google Chrome.app"
	"/Applications/Microsoft Word.app"
	"/Applications/Microsoft Powerpoint.app"
	"/Applications/Microsoft Excel.app"
	"/Applications/Microsoft Outlook.app"
	"/Applications/Microsoft OneNote.app"
	"/Applications/Microsoft Teams classic.app"
	"/System/Applications/System Settings.app"
	"/Applications/Self Service.app"
)

# Add applications to the Dock
for app in "${dockArray[@]}"; do
	dockutil --add "${app}" --no-restart
done

# Add additional items to the Dock
dockutil --add '~/Downloads' --view grid --display folder

# Set the desktop wallpaper
osascript -e 'tell application "Finder" to set desktop picture to POSIX file "/Library/Desktop Pictures/Woodleigh.jpg"'