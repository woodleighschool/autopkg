#!/bin/bash

# Runs all Jamf recipes
# Needs to be run in the root of the git project

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

jamfRecipeListPath=$(find . -name "*.jamf.recipe.yaml")

for recipe in $jamfRecipeListPath; do
	# Extract the NAME and Identifier using awk
	name=$(awk '/^Input:/{f=1} f && /NAME:/{sub(/NAME: /,""); print; exit}' "$recipe")
	identifier=$(awk '/^Identifier:/{print $2; exit}' "$recipe")

	# Check if name and identifier are found
	if [ -z "$name" ] || [ -z "$identifier" ]; then
		echo -e "${RED}Error: Unable to find NAME or Identifier in $recipe${NC}"
		continue
	fi

	echo -e "${CYAN}${BOLD}${name}: Building${YELLOW}"
	autopkg run "$identifier"
	if [ $? -eq 0 ]; then
		echo -e "${GREEN}${BOLD}${name}: Completed${NC}"
	else
		echo -e "${RED}${BOLD}${name}: Failed${NC}"
	fi
	echo ""
done
