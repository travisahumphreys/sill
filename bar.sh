#!/usr/bin/env bash

# --- Configuration ---
RESET="\e[0m"
WHITE="\e[1;37m"
GRAY="\e[0;90m"
BLUE="\e[1;34m"
GREEN="\e[1;32m"
RED="\e[1;31m"
YELLOW="\e[1;33m"

ICON_CLOCK="" # nf-fa-clock
ICON_MEM=""   # nf-fa-memory (or try  if that fails)
ICON_BAT=""   # nf-fa-battery_full

# --- Functions ---

get_workspaces() {
    # Check if hyprctl exists (prevent crash if not in Hyprland)
    if ! command -v hyprctl &>/dev/null; then
        echo "No Hyprland"
        return
    fi

    # Retrieve data once to minimize lag
    local monitors
    monitors=$(hyprctl monitors -j 2>/dev/null)
    local workspaces
    workspaces=$(hyprctl workspaces -j 2>/dev/null)

    # Safety check if jq is missing or hyprctl failed
    if [[ -z "$monitors" ]] || ! command -v jq &>/dev/null; then
        echo -e "${RED}Err${RESET}"
        return
    fi

    local active_ws
    active_ws=$(echo "$monitors" | jq -r '.[0].activeWorkspace.id')

    # Get all occupied workspace IDs as a single string for easy regex checking
    local occupied_ws
    occupied_ws=$(echo "$workspaces" | jq -r '.[].id')

    local ws_string=""

    for i in {1..9}; do
        if [ "$i" -eq "$active_ws" ]; then
            ws_string+="${BLUE}[${i}]${RESET} "
        elif [[ "$occupied_ws" =~ (^|[[:space:]])"$i"($|[[:space:]]) ]]; then
            ws_string+="${WHITE}${i}${RESET} "
        else
            ws_string+="${GRAY}${i}${RESET} "
        fi
    done

    # Trim trailing space
    echo -e "${ws_string% }"
}

get_time() {
    echo -e "${WHITE}$(date +'%H:%M')${RESET}"
}

get_battery() {
    if [ -d /sys/class/power_supply/BAT0 ]; then
        local cap
        cap=$(cat /sys/class/power_supply/BAT0/capacity)
        local color=$GREEN
        if [ "$cap" -lt 20 ]; then color=$RED; fi
        echo -e "${color}${ICON_BAT} ${cap}%${RESET}"
    elif [ -d /sys/class/power_supply/BAT1 ]; then
        # Fallback for some laptops where BAT0 is dead/internal
        local cap
        cap=$(cat /sys/class/power_supply/BAT1/capacity)
        echo -e "${GREEN}${ICON_BAT} ${cap}%${RESET}"
    else
        echo ""
    fi
}

get_mem() {
    local mem_used
    mem_used=$(awk '/MemTotal/ {t=$2} /MemAvailable/ {a=$2} END {printf "%.1f", (t-a)/1024/1024}' /proc/meminfo)
    echo -e "${YELLOW}${ICON_MEM} ${mem_used}G${RESET}"
}

# Strip ANSI codes for length calculation
strip_colors() {
    # -r prevents interpretation of backslashes, so we use sed to strip the escape sequences
    echo -e "$1" | sed "s/\x1B\[[0-9;]\{1,\}[A-Za-z]//g"
}

# --- Main Loop ---
while true; do
    # 1. Gather raw content
    WS_DATA=$(get_workspaces)
    LEFT_CONTENT=" $WS_DATA"
    RIGHT_CONTENT="$(get_mem)  |  $(get_battery)  |  $(get_time) "

    # 2. Strip colors to get actual text width
    #    (We must store in variable first to get length in bash)
    CLEAN_LEFT=$(strip_colors "$LEFT_CONTENT")
    CLEAN_RIGHT=$(strip_colors "$RIGHT_CONTENT")

    LEN_LEFT=${#CLEAN_LEFT}
    LEN_RIGHT=${#CLEAN_RIGHT}

    # 3. Get Terminal Width
    #    'tput cols' can fail in non-interactive shells, fallback to 100 if it does.
    TERM_WIDTH=$(tput cols 2>/dev/null || echo 100)

    # 4. Calculate Padding
    SPACES=$((TERM_WIDTH - LEN_LEFT - LEN_RIGHT))

    # Ensure spaces is never negative (prevents crashes on resize)
    if [ "$SPACES" -lt 1 ]; then SPACES=1; fi

    PADDING=$(printf "%${SPACES}s" "")

    # 5. Print
    #    \r to reset line, \c (or -n) to not print newline
    echo -e -n "\r${LEFT_CONTENT}${PADDING}${RIGHT_CONTENT}"

    sleep 1
done
