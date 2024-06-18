#!/bin/bash

defaults write com.apple.menuextra.clock Show24Hour -bool false
defaults write -g AppleICUForce12HourTime -bool true
defaults write -g AppleICUForce24HourTime -bool false
killall ControlCenter
