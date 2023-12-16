#!/bin/bash

# Loop to check if a user is logged in
until pgrep -q -x "Finder" && pgrep -q -x "Dock"; do
	sleep 1
done

sleep 3

##
# Set wallpaper
##

echo "Applying Wallpaper"
/usr/local/bin/desktoppr "/Library/Desktop Pictures/Woodleigh.jpg"

##
# Set Dock
##

# Removing all items from the dock
echo "Clearing Dock"
/usr/local/bin/dockutil --remove all --no-restart "${HOME}"
sleep 3

# find the correct teams version
if [ -d "/Applications/Microsoft Teams (work or school).app" ]; then
	TEAMSPATH="/Applications/Microsoft Teams (work or school).app"
elif [ -d "/Applications/Microsoft Teams classic.app" ]; then
	TEAMSPATH="/Applications/Microsoft Teams classic.app"
fi

# Setting up the dock array
IFS=$'\n'

dockArray=(
	"/System/Applications/Launchpad.app"
	"/System/Applications/Mission Control.app"
	"/Applications/Google Chrome.app"
	"/Applications/Microsoft Word.app"
	"/Applications/Microsoft Powerpoint.app"
	"/Applications/Microsoft Excel.app"
	"/Applications/Microsoft Outlook.app"
	"/Applications/Microsoft OneNote.app"
	"${TEAMSPATH}"
	"/System/Applications/System Settings.app"
	"/Applications/Self Service.app"
)

# Adding items to the dock
echo "Applying Dock"
for line in "${dockArray[@]}"; do
	/usr/local/bin/dockutil --add "$line" --no-restart "${HOME}"
	sleep 0.2
done

# customise dock, hide recents, minimise window into application
defaults write com.apple.dock minimize-to-application -bool true
defaults write com.apple.dock show-recents -bool false

# add downloads folder
/usr/local/bin/dockutil --add "${HOME}/Downloads" --view grid --display folder "${HOME}"

echo "Restarting Dock"
killall Dock
