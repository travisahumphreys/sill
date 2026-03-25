from colorer import fg, bg, fetch_palette

p = fetch_palette("./schemes/base16/catppuccin-mocha.yaml")
color = p.base09
foo = "bar"
fg_foo = fg(color, foo)

# you can also just call the color directly inside of the fg() or bg() functions:
bg_foo = bg(p.base01, foo)

nested_foo = fg(p.base00, bg(p.base06, foo))

emphatic_bar = fg(p.base08, f"foo {bg(p.base04, 'bar')} baz")

print("\n" + fg_foo + "\n")
print(bg_foo + "\n")
print(nested_foo + "\n")
print(emphatic_bar + "\n")

print(
    f"this is an {fg(p.base09, 'example')} of the {bg(p.base03, 'colorer')} including {fg(p.base08, bg(p.base04, 'nested strings'))} ."
)
