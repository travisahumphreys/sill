import yaml
from types import SimpleNamespace as simple_dict


def fetch_palette(path):
    expected_schema = ["system", "name", "author", "variant", "palette"]
    with open(path) as file:
        content = yaml.safe_load(file)
        if not all(key in content for key in expected_schema):
            raise Exception(
                """This module is intended to be used with base16/base24  
                color schemes from github.com/tinted-theming/schemes"""
            )
        elif not all(
            color[0] == "#" and len(color) == 7 for color in content["palette"].values()
        ):
            raise Exception("Wrong color format: Should be a hash followed by 6 digits")
        elif not all(is_hex(color) for color in content["palette"].values()):
            raise Exception("Not hexadecimal")
        else:
            return simple_dict(**hex_to_rgb(content["palette"]))


def is_hex(color):
    try:
        int(color[1:7], 16)
        return True
    except ValueError:
        return False


def hex_to_rgb(palette):
    palette_rgb = {
        key: [int(value[index : index + 2], 16) for index in range(1, 7, 2)]
        for key, value in palette.items()
    }
    # for key in palette:
    #     rgb = [int(palette[key][index : index + 2], 16) for index in range(1, 7, 2)]
    #     palette_rgb[key] = rgb
    return palette_rgb


def fg(color, string):
    rgb = ";".join(map(str, color))
    fg_start = f"\033[38;2;{rgb}m"
    reset = "\033[0m"
    color_fg = f"{fg_start}{string.replace(reset, reset + fg_start)}{reset}"
    return color_fg


def bg(color, string):
    rgb = ";".join(map(str, color))
    bg_start = f"\033[48;2;{rgb}m"
    reset = "\033[0m"
    color_bg = f"{bg_start}{string.replace(reset, reset + bg_start)}{reset}"
    return color_bg


def main():
    string = "▇▇▇▇▇▇▇▇▇▇"
    p = fetch_palette("./schemes/base16/everforest-dark-hard.yaml")

    print(
        f"this is a {fg(p.base09, 'test')} of the {bg(p.base08, 'colorer')} including {fg(p.base0E, bg(p.base02, 'nested strings'))} and resets."
    )
    print(
        f"this is {fg(p.base03, f'a longer nested test to see if something {bg(p.base08, "breaks")} with nested strings')} when used unconventionally"
    )
    for color in vars(p):
        print(f"{color}: {fg(vars(p)[color], string)}")


if __name__ == "__main__":
    main()
