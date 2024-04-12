#!/bin/bash

# Loop to check if a user is logged in
until pgrep -q -x "Finder" && pgrep -q -x "Dock"; do
	sleep 1
done

##
# Set wallpaper
##

osascript -e 'tell application "Finder" to set desktop picture to POSIX file "/Library/Desktop Pictures/Woodleigh.jpg"'

##
# Set Dock
##

dock_item() {
	printf '<dict><key>tile-data</key><dict><key>file-data</key><dict><key>_CFURLString</key><string>%s</string><key>_CFURLStringType</key><integer>0</integer></dict></dict></dict>', "$1"
}

defaults delete com.apple.dock persistent-apps

# find the correct teams version
if [ -d "/Applications/Microsoft Teams (work or school).app" ]; then
	TEAMSPATH="/Applications/Microsoft Teams (work or school).app"
elif [ -d "/Applications/Microsoft Teams classic.app" ]; then
	TEAMSPATH="/Applications/Microsoft Teams classic.app"
fi

defaults write com.apple.dock persistent-apps -array \
	"$(dock_item /System/Applications/Launchpad.app)" \
	"$(dock_item /System/Applications/Mission\ Control.app)" \
	"$(dock_item /Applications/Google\ Chrome.app)" \
	"$(dock_item /Applications/Microsoft\ Word.app)" \
	"$(dock_item /Applications/Microsoft\ Powerpoint.app)" \
	"$(dock_item /Applications/Microsoft\ Excel.app)" \
	"$(dock_item /Applications/Microsoft\ Outlook.app)" \
	"$(dock_item /Applications/Microsoft\ OneNote.app)" \
	"$(dock_item "${TEAMSPATH}")" \
	"$(dock_item /System/Applications/System\ Settings.app)" \
	"$(dock_item /Applications/Self\ Service.app)"

# customise dock, hide recents, minimise window into application
defaults write com.apple.dock minimize-to-application -bool true
defaults write com.apple.dock show-recents -bool false

killall Dock
