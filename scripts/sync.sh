#!/bin/bash
git fetch origin || exit 1 # just fetch the latest changes from the remote repository without merging, exit if it fails in case of network issues
git reset --mixed origin/main # move local branch pointer to match remote main without changing local directory

# '--mixed' resets the index but not the working directory, alligning local changes with origin main