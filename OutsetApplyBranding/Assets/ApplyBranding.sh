#!/bin/bash

# Loop to check if a user is logged in
while true; do
	loggedInUser=$(stat -f%Su /dev/console)
	if [[ "${loggedInUser}" != "root" ]]; then
		break
	fi
	sleep 1
done

# Wait for dock to start
while ! pgrep -x Dock >/dev/null; do
	sleep 1
done

# Removing all items from the dock
/usr/local/bin/dockutil --remove all --no-restart "${HOME}"
sleep 5

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
for line in ${dockArray[@]}; do
	sleep 0.1
	/usr/local/bin/dockutil --add "$line" --no-restart "${HOME}" >/dev/null
done

# customise dock, hide recents, minimise window into application
defaults write com.apple.dock minimize-to-application -bool true
defaults write com.apple.dock show-recents -bool false

# restart the dock, and add downloads folder
/usr/local/bin/dockutil --add "${HOME}/Downloads" --view grid --display folder "${HOME}" >/dev/null && echo "Restarting Dock"

# Applying wallpaper
echo "Applying Wallpaper"
/usr/local/bin/desktoppr "/Library/Desktop Pictures/Woodleigh.jpg"
