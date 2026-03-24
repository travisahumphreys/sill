import yaml

color_start = "\u001b[38;2;"
color_reset = "\033[0m"


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
            return hex_to_rgb(content["palette"])


def is_hex(color):
    try:
        int(color[1:7], 16)
        return True
    except ValueError:
        return False


def hex_to_rgb(palette):
    palette_rgb = {}
    for key in palette:
        rgb = [int(palette[key][index : index + 2], 16) for index in range(1, 7, 2)]
        palette_rgb[key] = rgb
    return palette_rgb


def format_ansi(string: str, palette, color_base):
    color_channels = palette[color_base]
    rgb = f"{';'.join(map(str, color_channels))}"
    return f"{color_start}{rgb}m{string}{color_reset}"


def main():
    string = "▇▇▇▇▇▇▇▇▇▇"
    palette = fetch_palette("./schemes/base24/gruvbox-dark.yaml")
    for color in palette:
        print(f"{color}: {palette[color]}")
        print(format_ansi(string, palette, color))


if __name__ == "__main__":
    main()
