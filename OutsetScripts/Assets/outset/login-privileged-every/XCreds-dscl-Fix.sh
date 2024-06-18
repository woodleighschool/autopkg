#!/bin/bash

loggedInUser=$(stat -f "%Su" /dev/console)

# Xcreds temp fix for accounts not created via login
dscl . -create /Users/"${loggedInUser}" 'dsAttrTypeNative:_xcreds_oidc_username' "${loggedInUser}"
dscl . -create /Users/"${loggedInUser}" 'dsAttrTypeNative:_xcreds_activedirectory_kerberosPrincipal' "${loggedInUser}"@WOODLEIGHSCHOOL.NET
