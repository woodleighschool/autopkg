#!/bin/bash

# Function to check if a user is a FileVault user
isFileVaultUser() {
	local user=$1
	local users=$(fdesetup list)
	if echo "$users" | grep -q "^$user,"; then
		return 0
	else
		return 1
	fi
}

# Check if the current user is woodmin
if [ "$(stat -f%Su /dev/console)" == "woodmin" ]; then
	# Check if woodmin is a FileVault user
	if isFileVaultUser "woodmin"; then
		if /usr/bin/fdesetup remove -user woodmin; then
			echo "Disabled FileVault for Woodmin."
		else
			echo "Failed to disable FileVault for Woodmin."
		fi
	else
		echo "Woodmin is not a FileVault user (or yet...)."
		exit 1
	fi
fi
