#!/usr/bin/env python3

import json
import os
import re
import select
import socket
import time

colors = {  # TODO: base16 color support?
    "white": "\033[1;37m",
    "black": "\033[0;30m",
    "gray": "\033[0;90m",
    "blue": "\033[1;34m",
    "green": "\033[1;32m",
    "red": "\033[1;31m",
    "yellow": "\033[1;33m",
    "bg_blue": "\033[44m",
}

icons = {
    "clock": " ",
    "mem": "",
    "bat": "",  # TODO: Nested Dict with battery level icons
    "ac": "󱐥",
    "charged": "󰚥",
}
# "bat": {
#   "draining": ['󰂃 ', '󰁺 ', '󰁻 ', '󰁼 ', '󰁽 ', '󰁾 ', '󰁿 ', '󰂀 ', '󰂁 ', '󰂂 ', '󰁹 '],
#   "charging": ['󱐥 ', '󰢜 ', '󰂆 ', '󰂇 ', '󰂈 ', '󰢝 ', '󰂉 ', '󰢞 ', '󰂊 ', '󰂋 ', '󰂅 ']
# }

reset = "\033[0m"

HYPR_DIR = (
    f"{os.environ['XDG_RUNTIME_DIR']}/hypr/{os.environ['HYPRLAND_INSTANCE_SIGNATURE']}"
)
SOCKET = f"{HYPR_DIR}/.socket.sock"
SOCKET2 = f"{HYPR_DIR}/.socket2.sock"


def hyprctl(command: str) -> str:
    """Send a request to socket.sock and return the JSON response."""
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
        sock.connect(SOCKET)
        sock.sendall(f"[j]/{command}".encode())
        chunks = []
        while chunk := sock.recv(4096):
            chunks.append(chunk)
        return b"".join(chunks).decode()


def strip_ansi(s: str) -> str:
    return re.sub(r"\033\[[0-9;]*[A-Za-z]", "", s)


def fmt_workspaces(occupied: set[int], active: int) -> str:
    parts = []
    for i in range(1, 10):
        if i == active:
            parts.append(
                f"{colors['blue']}◖{colors['black']}{colors['bg_blue']}{i}{reset}{colors['blue']}◗{reset}"
            )
        elif i in occupied:
            parts.append(f"{colors['white']}{i}{reset}")
        # else:
        #     parts.append(f"{colors['gray']}{i}{reset}")
    return " ".join(parts)


def get_time() -> str:
    return f"{colors['white']}{icons['clock']}{time.strftime('%H:%M')}{reset}"


def get_battery() -> str:
    base = "/sys/class/power_supply/BAT0"
    cap_path = f"{base}/capacity"
    status_path = f"{base}/status"

    if not (os.path.exists(cap_path) and os.path.exists(status_path)):
        return ""

    with open(cap_path) as f:
        cap = int(f.read().strip())
    with open(status_path) as f:
        status = f.read().strip()

    color = colors["red"] if cap < 20 else colors["green"]

    if status == "Charging":
        return f"{color}{icons['ac']} {cap}%{reset}"
    elif status == "Not charging":
        return f"{color}{icons['charged']} {cap}%{reset}"
    else:
        return f"{color}{icons['bat']} {cap}%{reset}"


def get_mem() -> str:
    info = {}
    with open("/proc/meminfo") as f:
        for line in f:
            parts = line.split()
            if parts[0] in ("MemTotal:", "MemAvailable:"):
                info[parts[0]] = int(parts[1])
    used = (info["MemTotal:"] - info["MemAvailable:"]) / 1024 / 1024
    return f"{colors['yellow']}{icons['mem']} {used:.1f}G{reset}"


def render(occupied: set[int], active: int, win_title: str):
    left = f" {fmt_workspaces(occupied, active)}"

    title = f" ---- {win_title}"

    right_parts = [get_mem()]
    bat = get_battery()
    if bat:
        right_parts.append(bat)
    right_parts.append(get_time())
    right = "  |  ".join(right_parts) + " "

    try:
        term_width = os.get_terminal_size().columns
    except OSError:
        term_width = 100

    spaces = max(
        1, term_width - len(strip_ansi(left)) - len(title) - len(strip_ansi(right))
    )
    print(
        f"\r{left}{colors['white']}{title}{reset}{' ' * spaces}{right}",  # TODO: break out title formatting to function
        end="",
        flush=True,
    )


def main():
    # Initial state via IPC
    monitors = json.loads(hyprctl("monitors"))
    active_ws = monitors[0]["activeWorkspace"]["id"]

    window_data = json.loads(hyprctl("activewindow"))
    active_win = window_data.get("title", "")

    ws_data = json.loads(hyprctl("workspaces"))
    occupied = {ws["id"] for ws in ws_data if ws["id"] > 0}

    render(occupied, active_ws, active_win)

    # Event loop: listen on socket2 for workspace changes, redraw every 1s regardless
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
        sock.connect(SOCKET2)
        sock.setblocking(False)
        buf = ""

        while True:
            ready, _, _ = select.select([sock], [], [], 1.0)

            if ready:
                data = sock.recv(4096).decode()
                if not data:
                    break
                buf += data
                while "\n" in buf:
                    line, buf = buf.split("\n", 1)
                    event, _, payload = line.partition(">>")

                    if event == "workspacev2":
                        ws_id, _, _ = payload.partition(",")
                        active_ws = int(ws_id)

                    elif event == "workspace":
                        try:
                            active_ws = int(payload)
                        except ValueError:
                            pass

                    elif event == "createworkspacev2":
                        ws_id, _, _ = payload.partition(",")
                        ws_id = int(ws_id)
                        if ws_id > 0:
                            occupied.add(ws_id)

                    elif event == "createworkspace":
                        try:
                            ws_id = int(payload)
                            if ws_id > 0:
                                occupied.add(ws_id)
                        except ValueError:
                            pass

                    elif event == "destroyworkspacev2":
                        ws_id, _, _ = payload.partition(",")
                        occupied.discard(int(ws_id))

                    elif event == "destroyworkspace":
                        try:
                            occupied.discard(int(payload))
                        except ValueError:
                            pass

                    elif event == "activewindow":
                        try:
                            _, _, active_win = payload.partition(",")
                        except ValueError:
                            pass

            render(occupied, active_ws, active_win)


if __name__ == "__main__":
    main()
