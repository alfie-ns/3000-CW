#!/bin/bash

# Git Pull-Push Commits Script

git pull origin main || exit 1

set -e  # Exit immediately if a command exits with a non-zero status

# Function to print bold text
print_bold() {
    echo -e "\033[1m$1\033[0m"
}

# Function to get commit importance and custom message
get_commit_details() {
    local importance_text
    while true; do
        echo -n "Enter the importance (1-5): " >&2
        read -rsn1 importance # read a single character: -r: don't interpret backslashes(raw input); -s: don't echo input; -n1: read only one character
        echo >&2

        case $importance in
            1) importance_text="Trivial"; break;;
            2) importance_text="Minor"; break;;
            3) importance_text="Moderate"; break;;
            4) importance_text="Significant"; break;;
            5) importance_text="Milestone"; break;;
            *) echo "Invalid input. Please try again." >&2;;
        esac
    done

    echo -n "Enter a custom message for the commit: " >&2
    read custom_message
    echo >&2

    if [ "$importance_text" = "Trivial" ]; then
        echo "${importance_text}"
    else
        echo "${importance_text}: ${custom_message}"
    fi
}

# Function to selectively add files to staging
selective_add() {
    print_bold "\nUnstaged changes:"
    git status --porcelain | grep -E '^\s*[\?M]' | sed 's/^...//'
    # the above command lists all untracked and modified files;
    # untracked(?) and modified(M); the final sed command removes
    # the first three characters which are the status flags.
    while true; do
        echo -n "Enter file/directory to add, 'all' (or 'done' to finish): "
        read item

        if [ "$item" = "done" ]; then
            break
        elif [ "$item" = "all" ]; then
            git add .
            echo "Added all changes"
            break
        elif [ -e "$item" ]; then
            git add "$item"
            echo "Added: $item"
        else
            echo "File/directory not found. Please try again."
        fi
    done
}

# Main Execution --------------------------------------------

# 1- Selectively add changes
selective_add

# 2- Get commit importance and custom message
print_bold "\nCommit importance:" >&2
echo "1. Trivial" >&2
echo "2. Minor" >&2
echo "3. Moderate" >&2
echo "4. Significant" >&2
echo -e "5. Milestone\n" >&2
commit_message=$(get_commit_details)


# 3- Commit and push changes
if git commit -m "$commit_message"; then
    echo "Changes committed successfully" >&2
    if git push origin main; then
        echo -e '\nLocal repo pushed to remote origin\n' >&2
        print_bold "Commit message: $commit_message" >&2
        exit 0
    else
        echo "Error: Failed to push to remote..." >&2
        exit 1
    fi
else
    echo "Error: Failed to commit changes..." >&2
    exit 1
fi