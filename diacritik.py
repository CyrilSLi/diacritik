import json, os, subprocess, sys, time, tkinter as tk
global mode

# Ensure only one instance is running
def excepthook (exc_type, exc_value, exc_traceback):
    try:
        os.rmdir ("/tmp/diacritik/running")
    except FileNotFoundError:
        print ("Cannot remove lock file")
    sys.__excepthook__ (exc_type, exc_value, exc_traceback)
sys.excepthook = excepthook

try:
    os.makedirs ("/tmp/diacritik/running")
except FileExistsError:
    raise SystemExit ("Duplicate instance")

if not os.path.exists ("/tmp/diacritik/mode"):
    with open ("/tmp/diacritik/mode", "w") as f:
        f.write ("user")
    mode = "user" # user or pinyin
else:
    with open ("/tmp/diacritik/mode") as f:
        mode = f.read ().strip ()

mode_text = lambda: {"user": "Type a key:", "pinyin": "Type pinyin:"} [mode]
mode_font = lambda: {"user": ("Noto Sans Mono", 32), "pinyin": ("Noto Sans Mono", 32)} [mode] # CHANGE FONT AND SIZE HERE

with open (os.path.join (os.path.dirname (os.path.abspath (__file__)), "keymap.json")) as f:
    key_map = json.load (f)
with open (os.path.join (os.path.dirname (os.path.abspath (__file__)), "methods.json")) as f:
    methods = json.load (f)

app = tk.Tk ()
app.title ("Diacritik")
app.configure (padx = 10, pady = 10)

key_label = tk.Label (app)
opt_label = tk.Label (app)

pys = {} # Pinyin State
def setup ():
    global pys, selecting, app
    selecting = False
    pys.update ({ # Pinyin State
        "page": 1,
        "options": [], # [[char, length], ...]
        "matched": "",
        "unmatched": "",
        "cache": pys.get ("cache", {}) # Preserve cache across mode switches
    })
    key_label.config (text = mode_text (), fg = "black", font = mode_font ())
    opt_label.config (text = "[ ]" * 10, fg = "black", font = mode_font ())

setup ()
key_label.pack ()
opt_label.pack ()

def req_pinyin ():
    import requests as r
    global pys, app

    if not pys ["unmatched"]:
        pys ["page"] = 1
        return [[" ", 0] for i in range (9)]

    offset = pys ["page"] * 9
    if pys ["unmatched"] not in pys ["cache"] or len (pys ["cache"] [pys ["unmatched"]]) < offset:
        try:
            res = r.get ("https://inputtools.google.com/request?text={}&itc=zh-t-i0-pinyin&num={}&ie=utf-8&oe=utf-8".format (
                pys ["unmatched"], str (offset)
            )).json ()
            if res [0] != "SUCCESS":
                raise Exception
        except:
            key_label.config (text = "Failed to fetch pinyin", fg = "red")
            return

        offset = min (offset, len (res [1] [0] [1]))
        cache = [[res [1] [0] [1] [i], res [1] [0] [3].get ("matched_length", [len (pys ["unmatched"])] * offset) [i]] for i in range (offset)]
        cache.extend ([[" ", 0] for i in range (8 - (len (cache) - 1))]) # Pad to 9
        offset = len (cache)
        pys ["page"] = -(-offset // 9)
        pys ["cache"] [pys ["unmatched"]] = cache

    return pys ["cache"] [pys ["unmatched"]] [offset - 9 : offset]

def key_user (event, key):
    global selecting, key_map, app

    if selecting and key in "1234567890" [ : len (key_map [selecting])]:
        selecting = key_map [selecting] ["1234567890".index (key)]
        app.destroy ()
        return
    elif selecting:
        opt_label.config (text = "[ ]" * 10)
        selecting = False

    if key in key_map:
        key_label.config (text = key, fg = "green")
        opt_label.config (text = "[" + "][".join ((key_map [key] + " " * 10) [ : 10]) + "]")
        selecting = key
    else:
        key_label.config (text = f"{key} not found", fg = "red")

def key_pinyin (event, key):
    global selecting, pys, app

    if key in ("Up", "Left"):
        if len (pys ["options"]) > 1 and pys ["page"] > 1:
            pys ["page"] -= 1
        else:
            return
    elif key in ("Down", "Right"):
        if len (pys ["options"]) > 1:
            pys ["page"] += 1
        else:
            return
    else:
        pys ["page"] = 1
        if key == "BackSpace":
            if pys ["unmatched"]:
                pys ["unmatched"] = pys ["unmatched"] [ : -1]
            elif pys ["matched"]:
                pys ["matched"] = pys ["matched"] [ : -1]
            else:
                return
        elif key in "abcdefghijklmnopqrstuvwxyz":
            pys ["unmatched"] += key
        elif key in "123456789":
            key = int (key) - 1
            if len (pys ["options"]) > key + 1 and pys ["options"] [key] [1] > 0:
                pys ["matched"] += pys ["options"] [key] [0]
                pys ["unmatched"] = pys ["unmatched"] [pys ["options"] [key] [1] : ]
        else:
            return

    pys ["options"] = req_pinyin ()
    if pys ["options"]:
        selecting = pys ["matched"] + pys ["unmatched"]
        key_label.config (text = selecting, fg = "black")
        opt_label.config (text = "[" + "][".join ([i [0] for i in pys ["options"]] + [str (pys ["page"] if pys ["options"] [0] [0].strip () else " ")]) + "]")

def display_key (event):
    global first_key, mode, app, selecting

    if event.keysym in ("Control_L", "Control_R"):
        mode = {"user": "pinyin", "pinyin": "user"} [mode]
        setup ()
        return
    elif mode == "pinyin" and event.keysym in ("Up", "Down", "Left", "Right", "BackSpace"): # Passthrough for pinyin
        key_pinyin (event, event.keysym)
        return
    first_key = False

    key = event.char
    if not key:
        return
    elif ord (key) in (13, 27): # Enter or Escape
        if ord (key) == 27:
            selecting = False
        app.destroy ()
        return
    elif ord (key) < 32 or ord (key) > 126:
        return # Ignore non-printable characters
    {"user": key_user, "pinyin": key_pinyin} [mode] (event, key)

app.bind ("<Key>", display_key)
app.mainloop ()

with open ("/tmp/diacritik/mode", "w") as f:
    f.write (mode)
os.rmdir ("/tmp/diacritik/running")
if not selecting:
    raise SystemExit

focused = subprocess.run (methods ["__cmd__"], capture_output = True, shell = True)
focused.check_returncode ()
focused = focused.stdout.decode ().strip ()
method = methods.get (focused, methods ["__default__"])

for i in selecting:
    if method == "char":
        os.system (f"wtype {i}")
    elif method == "hex":
        subprocess.run (f'wtype -M ctrl -M shift -k U -m ctrl -m shift {" -k ".join (hex (ord (i)) [2 : ])} -k Return'.split ()).check_returncode ()
    time.sleep (0.05)
