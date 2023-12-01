#!/bin/bash

# Loop to check if a user is logged in
while true; do
	loggedInUser=$(stat -f%Su /dev/console)
	if [[ "${loggedInUser}" != "root" ]]; then
		break
	fi
	sleep 1
done

# Loop to wait for Dock process
while true; do
	myUser=$(id -un)
	dockcheck=$(ps -ef | grep -v 'grep' | grep /System/Library/CoreServices/Dock.app/Contents/MacOS/Dock)

	if [[ -n "${dockcheck}" ]]; then
		break
	fi
	sleep 1
done

# Setting up the dock array and user home directory
IFS=$'\n'
userHome=$(dscl . -read /Users/${loggedInUser} NFSHomeDirectory | awk '{print $2}')

# Removing all items from the dock
dockutil --remove all --no-restart "$userHome"
sleep 2

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

# Adding items to the dock
for line in ${dockArray[@]}; do
	dockutil --add "$line" --no-restart "$userHome"
done

dockutil --add "$userHome/Downloads" --view grid --display folder "$userHome"
sudo killall Dock

# Applying wallpaper
launchctl asuser $(id -u "$loggedInUser") desktoppr /Library/Desktop\ Pictures/Woodleigh.jpg
