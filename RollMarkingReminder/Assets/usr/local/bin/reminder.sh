#!/bin/bash
#set -x
# Set debug mode (true/false)
debug=false

send_notification() {
	dialog --notification --title "Roll Marking Reminder" --message "Have you marked your roll?\nHave you updated students who arrived late?"
}

is_weekday() {
	day_of_week=$(date +%u) # 1 = Monday, 7 = Sunday
	if [[ $day_of_week -ge 1 && $day_of_week -le 5 ]]; then
		return 0 # weekday
	else
		return 1 # weekend
	fi
}

while true; do
	# Calculate time until the next full minute
	seconds_until_next_minute=$((60 - $(date +%S)))
	sleep $seconds_until_next_minute

	# Get the IP address of en0
	ip_address=$(ifconfig en0 | awk '/inet /{print $2}')

	# Check if it's a weekday
	if is_weekday; then
		# If debug mode is enabled, instantly send the notifications
		if $debug; then
			echo "Debug mode enabled. Sending notifications instantly."
			send_notification
		else
			# Check if the IP address is within the staff subnet
			if [[ "${ip_address}" =~ ^10\.10\.(4|5|6|7|9)\.[0-9]+$ ]]; then
				current_time=$(date +"%H:%M")
				if [[ "$current_time" == "11:20" || "$current_time" == "15:30" ]]; then
					send_notification
				fi
			fi
		fi
	else
		if $debug; then
			echo "Debug mode enabled, but today is a weekend. Skipping notification."
		fi
	fi
done
