#!/bin/bash

# Try unlock sudoers
if ! chflags noschg /etc/sudoers; then
	if ! chflags unschg /etc/sudoers; then
		echo "Could not unlock sudoers."
		exit 1
	fi
fi

# Overwrite /etc/sudoers so that only root, tokenadmin, woodmin and Cadmin are permitted to use sudo
cat >/etc/sudoers <<'EOF'
    ##
    # Override built-in defaults
    ##
    Defaults    env_reset
    Defaults    env_keep += "BLOCKSIZE"
    Defaults    env_keep += "COLORFGBG COLORTERM"
    Defaults    env_keep += "__CF_USER_TEXT_ENCODING"
    Defaults    env_keep += "CHARSET LANG LANGUAGE LC_ALL LC_COLLATE LC_CTYPE"
    Defaults    env_keep += "LC_MESSAGES LC_MONETARY LC_NUMERIC LC_TIME"
    Defaults    env_keep += "LINES COLUMNS"
    Defaults    env_keep += "LSCOLORS"
    Defaults    env_keep += "SSH_AUTH_SOCK"
    Defaults    env_keep += "TZ"
    Defaults    env_keep += "DISPLAY XAUTHORIZATION XAUTHORITY"
    Defaults    env_keep += "EDITOR VISUAL"
    Defaults    env_keep += "HOME MAIL"

    Defaults    lecture_file = "/etc/sudo_lecture"

    root        ALL = (ALL) ALL
    tokenadmin  ALL = (ALL) ALL
    woodmin     ALL = (ALL) ALL
    Cadmin      ALL = (ALL) ALL
EOF

# Lock sudoers so it can't be modified without already having sudo
chflags schg /etc/sudoers
chflags schg /etc/sudoers.d

# Remove root's password (disable password login)
dscl . -passwd /Users/root ''
