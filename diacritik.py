import tkinter as tk
app = tk.Tk ()
app.title ("Diacritik")
app.update ()

import json, os, shlex, subprocess, requests as r, sys, threading, time
global mode, threadpool, r

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

app.configure (padx = 10, pady = 10)
key_label = tk.Label (app)
opt_label = tk.Label (app)

pys = {} # Pinyin State
def setup ():
    global pys, selecting, app, threadpool
    selecting = False
    pys.update ({ # Pinyin State
        "page": 1,
        "options": [], # [[char, length], ...]
        "matched": "",
        "unmatched": "",
        "raw_input": False,
        "cache": pys.get ("cache", {}) # Preserve cache across mode switches
    })
    threadpool = []
    key_label.config (text = mode_text (), fg = "black", font = mode_font ())
    opt_label.config (text = "[ ]" * 10, fg = "black", font = mode_font ())

setup ()
key_label.pack ()
opt_label.pack ()

def google_pinyin (chars, offset):
    global r
    res = r.get ("https://inputtools.google.com/request?text={}&itc=zh-t-i0-pinyin&num={}&ie=utf-8&oe=utf-8".format (
        chars, str (offset)
    )).json ()
    if res [0] != "SUCCESS":
        raise Exception
    offset = min (offset, len (res [1] [0] [1]))
    cache = [[res [1] [0] [1] [i], res [1] [0] [3].get ("matched_length", [len (chars)] * offset) [i]] for i in range (offset)]
    return offset, cache

def baidu_pinyin (chars, offset):
    global r
    res = r.get ("https://olime.baidu.com/py?input={}&inputtype=py".format (
        chars
    )).json () ["0"] [0]
    offset = min (offset, len (res))
    cache = [[res [i] [0], len (chars)] for i in range (offset)] # Always full match
    return offset, cache

pinyin_providers = ("google", "baidu")
provider_funcs = {
    "google": google_pinyin,
    "baidu": baidu_pinyin
}
pinyin_provider = methods.get ("__pinyin_provider__", "google").lower ()

def next_provider ():
    global pinyin_providers, pinyin_provider
    pinyin_provider = pinyin_providers [(pinyin_providers.index (pinyin_provider) + 1) % len (pinyin_providers)]
    key_label.config (text = f"Using {pinyin_provider} pinyin", fg = "black")

def req_pinyin (chars):
    global pys, app, pinyin_provider, provider_funcs, selecting

    if pys ["raw_input"]:
        pys ["matched"] = chars
        pys ["unmatched"] = ""
        key_label.config (text = pys ["matched"], fg = "black")
        opt_label.config (text = "Raw Input Mode")
        selecting = pys ["matched"]
        return
    elif not chars:
        pys ["page"] = 1
        options = [[" ", 0] for i in range (9)]
    else:
        offset = pys ["page"] * 9
        if chars not in pys ["cache"] or len (pys ["cache"] [chars]) < offset:
            try:
                offset, cache = provider_funcs [pinyin_provider] (chars, offset)
            except Exception as e:
                key_label.config (text = "Failed to fetch pinyin", fg = "red")
                return

            cache.extend ([[" ", 0] for i in range (8 - (len (cache) - 1))]) # Pad to 9
            offset = len (cache)
            pys ["page"] = -(-offset // 9)
            pys ["cache"] [chars] = cache
        options = pys ["cache"] [chars] [offset - 9 : offset]

    pys ["options"] = options
    if pys ["options"]:
        selecting = pys ["matched"] + pys ["unmatched"]
        key_label.config (text = selecting, fg = "black")
        opt_label.config (text = "[" + "][".join ([i [0] for i in pys ["options"]] + [str (pys ["page"] if pys ["options"] [0] [0].strip () else " ")]) + "]")
    # print ("req_pinyin finished", chars)

def update_pool ():
    global pys, threadpool
    while threadpool:
        threadpool = [t for t in threadpool if t.is_alive ()]
        time.sleep (0.1)
    # print ("Pool cleared")
    req_pinyin (pys [("unmatched", "matched") [pys ["raw_input"]]])

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
        opt_label.config (text = "[ ]" * 10)

def key_pinyin (event, key):
    global selecting, pys, app, threadpool

    if pys ["raw_input"] and key not in ("Tab", "BackSpace"):
        req_pinyin (pys ["matched"] + event.char)
        return
    elif key in ("Up", "Left"):
        if len (pys ["options"]) > 1 and pys ["page"] > 1:
            pys ["page"] -= 1
        else:
            return
    elif key in ("Down", "Right"):
        if len (pys ["options"]) > 1:
            pys ["page"] += 1
        else:
            return
    elif key == "Tab":
        pys ["raw_input"] = not pys ["raw_input"]
        if pys ["raw_input"]:
            req_pinyin (pys ["matched"] + pys ["unmatched"])
        else:
            req_pinyin ("")
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
            if pys ["raw_input"]:
                req_pinyin (pys ["matched"])
                return
        elif key in "abcdefghijklmnopqrstuvwxyz":
            pys ["unmatched"] += key
        elif key in "123456789" and selecting and pys ["unmatched"]:
            key = int (key) - 1
            if len (pys ["options"]) > key and pys ["options"] [key] [1] > 0:
                pys ["matched"] += pys ["options"] [key] [0]
                pys ["unmatched"] = pys ["unmatched"] [pys ["options"] [key] [1] : ]
            else:
                pys ["unmatched"] = ""
        else:
            selecting = False
            key_user (event, key)
            pys ["unmatched"] = selecting if selecting else ""
            if selecting:
                pys ["options"] = [[i, 1] for i in key_map [selecting]] + [["", 0] for i in range (9 - len (key_map [selecting]))]
            return

    t = threading.Thread (target = req_pinyin, args = (pys ["unmatched"], ))
    t.start ()
    threadpool.append (t)
    if len (threadpool) == 1:
        threading.Thread (target = update_pool).start () # Resolve out-of-sync issues

def display_key (event):
    global mode, app, selecting, pys

    if event.keysym in ("Control_L", "Control_R") and not pys ["raw_input"]:
        mode = {"user": "pinyin", "pinyin": "user"} [mode]
        setup ()
        return
    elif event.keysym in ("Alt_L", "Alt_R") and not pys ["raw_input"]:
        next_provider ()
        return
    elif mode == "pinyin" and event.keysym in ("Up", "Down", "Left", "Right", "BackSpace", "Tab"): # Passthrough for pinyin
        key_pinyin (event, event.keysym)
        return

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
delay = 0.05 # Delay between characters

with open ("/tmp/diacritik/mode", "w") as f:
    f.write (mode)
os.rmdir ("/tmp/diacritik/running")
if not selecting:
    raise SystemExit

focused = subprocess.run (methods ["__cmd__"], capture_output = True, shell = True)
focused.check_returncode ()
focused = focused.stdout.decode ().strip ()
method = methods.get (focused, methods ["__default__"])

if type (method) == dict:
    method, delay = method.get ("method", methods ["__default__"]), method.get ("delay", delay)

for i in selecting:
    if method == "char":
        subprocess.run (["wtype", "--", i])
    elif method == "hex":
        subprocess.run (f'wtype -M ctrl -M shift -k U -m ctrl -m shift {" -k ".join (hex (ord (i)) [2 : ])} -k Return'.split ())
    time.sleep (delay)
