# Diacritik - Input framework-independent pinyin IME and diacritic input for Wayland

Diacritik is a simple Python Tkinter application which provides macOS-style diacritic entry and Google Pinyin-powered pinyin input for Linux + Wayland. It is designed to be able to work without input frameworks (e.g. `IBus`, `fcitx`) and can be used with any WM/DE with most applications.

## Dependencies

- Python 3
- tkinter
- requests (only for pinyin)
- wtype

By default this script uses the **Noto Sans Mono** font which provides good monospace support for both Latin and CJK characters. **Please install the font before running the script**, or change the font at the commented line in `diacritik.py`.

## Installation

Bind a key combination to the `diacritik.py` script. If you are using a tiling window manager, also set windows with a title of `Diacritik` to floating.

## Inserting method

Due to complications in (X)Wayland, different applications may require different methods of inserting characters. Currently, the following methods are supported:
- `hex` - Insert the character(s) by simulating hex code input using Ctrl+Shift+U.
- `char` - Directly types the character(s).

**Both methods require `wtype` to be installed. Focus on the desired input field before using the script.**

The script includes a function which checks for the focused application and selects the appropriate method. Configuration is stored in `methods.json`, which includes the following keys:
- `__default__` - The default method to use.
- `__cmd__` - A shell command to find the app ID of the focused window.
- A list of app IDs with the method to use for each.

## Usage

At any point,
- Press either `control` keys to switch between user and pinyin modes.
- Press `escape` (or kill the window) to exit the script without typing anything.

## User mode

This mode associates base letters with a set of other characters. It is useful for typing diacritics, but can be used for any other characters as well.

### Keymap

The keymap is stored as an object in `keymap.json`. The default keymap is inspired by macOS, but can be customized to your liking. The keys of the object are single characters representing the base letter (an ASCII character), and the values are strings of possible options (any Unicode characters, max length 10). Options will be shown from left to right, selected using the number keys.

### User flow

- Enter the base letter, using `shift` if necessary.
- If the base letter is defined in the keymap:
  - The available options will be displayed.
  - Press the number key corresponding to the desired option, **or**
  - Press `enter` to type the base letter, **or**
  - Press any other key to switch to that base letter.
- Else, an error message will be displayed. Retry with a different base letter.

## Pinyin mode

This mode uses the Google Pinyin endpoint to input (currently only Simplified Chinese) pinyin, which is then typed out the same way as in user mode. The requests are cached in memory to reduce latency and cleared when the script exits.

### User flow

- Enter a letter in the alphabet.
- The chacter options (max length 9) will be displayed, with the 10th space representing the current page number.
- Do one of the following, or keep typing letters to match longer pinyin sequences:
  - Press the `down` or `right` arrow keys to go to the next page, **or**
  - Press the `up` or `left` arrow keys to go to the previous page, **or**
  - Press the number key (1-9) corresponding to a match, which adds the matched character(s) to a buffer, **or**
  - Press `enter` to type out the buffer along with any unmatched letters, **or**
  - Press `backspace` to remove unmatched letters (or the buffer if there are no unmatched letters)