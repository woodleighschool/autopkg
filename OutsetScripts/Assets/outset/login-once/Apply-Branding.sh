#!/bin/bash

# Wait for the Dock process to start
echo "Waiting for Dock"
until pgrep -q -x "Dock"; do
	sleep 1
done

if ! defaults read io.macadmins.Outset run_once | grep -q 'ApplyBranding.sh'; then

	# Set Wallpaper
	echo "Applying wallpaper"
	osascript -e 'tell application "Finder" to set desktop picture to POSIX file "/Library/Desktop Pictures/Woodleigh.jpg"'

	# Function to format the dock item XML
	dock_item() {
		printf '<dict><key>tile-data</key><dict><key>file-data</key><dict><key>_CFURLString</key><string>%s</string><key>_CFURLStringType</key><integer>0</integer></dict></dict></dict>', "$1"
	}

	# Function to setup Dock
	setup_dock() {
		defaults delete com.apple.dock persistent-apps

		if [ -d "/Applications/Microsoft Teams.app" ]; then
			TEAMSPATH="/Applications/Microsoft Teams.app"
		elif [ -d "/Applications/Microsoft Teams (work or school).app" ]; then
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
			"$(dock_item /Applications/Self\ Service.app)" \
			"$(dock_item /Applications/Vivi.app)"

		defaults write com.apple.dock minimize-to-application -bool true
		defaults write com.apple.dock show-recents -bool false

		killall Dock
	}

	# Attempt to setup Dock
	setup_dock
	sleep 1

	# Just do what you're told to do, Dock!
	for i in {1..5}; do
		sleep 5
		if defaults read com.apple.dock persistent-apps | grep -qi "Self Service"; then
			echo "Dock setup confirmed."
			break
		else
			echo "Dock setup not confirmed, retrying."
			setup_dock
		fi
	done
fi
