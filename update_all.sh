#!/bin/bash

# Runs all Jamf recipes

# Change directory
cd ~/Library/AutoPkg/RecipeRepos/com.github.woodleighschool.autopkg

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

jamfRecipeListPath=$(find . -name "*.jamf.recipe.yaml")

# Initialize an empty string for identifiers
identifiers=""

for recipe in $jamfRecipeListPath; do
	identifier=$(awk '/^Identifier:/{print $2; exit}' "$recipe")

	if [ -z "$identifier" ]; then
		echo -e "${RED}Error: Unable to find Identifier in $recipe${NC}"
		continue
	fi

	# Add identifier to the list
	identifiers="$identifiers $identifier"
done

# Run autopkg with all identifiers
echo -e "${CYAN}${BOLD}Running autopkg for all recipes${YELLOW}"
echo "autopkg run $identifiers"
if [ $? -eq 0 ]; then
	echo -e "${GREEN}${BOLD}All recipes completed successfully${NC}"
else
	echo -e "${RED}${BOLD}Some recipes failed${NC}"
fi
