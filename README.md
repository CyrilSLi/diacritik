# Diacritik

Diacritik is a simple Python Tkinter application which provides macOS-style diacritic entry for Linux + Wayland. To insert a character, first type the base letter, then choose one of the options presented using a number key.

## Dependencies

- Python 3
- Tkinter
- wtype

## Installation

Bind a key combination to the `diacritik.py` script. If you are using a tiling window manager, also set windows with a title of `Diacritik` to floating.

## Keymap

The keymap is stored as an object in `keymap.json`. The default keymap is copied from macOS, but can be customized to your liking. The keys of the object are single characters representing the base letter, and the values are strings of possible options with a maximum length of 10. Options will be shown from left to right.

## Inserting method

Due to complications in (X)Wayland, different applications may require different methods of inserting characters. Currently, the following methods are supported:
- `hex` - Insert the character by simulating hex code input using Ctrl+Shift+U.
- `char` - Directly types the character.

**Both methods require `wtype` to be installed.**

The script includes a function which checks for the focused application and selects the appropriate method. Configuration is stored in `methods.json`, which includes the following keys:
- `__default__` - The default method to use.
- `__cmd__` - A shell command to find the app ID of the focused window.
- A list of app IDs with the method to use for each.