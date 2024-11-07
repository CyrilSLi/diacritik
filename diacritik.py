import json, os, subprocess, tkinter as tk

with open (os.path.join (os.path.dirname (os.path.abspath (__file__)), "keymap.json")) as f:
    key_map = json.load (f)
with open (os.path.join (os.path.dirname (os.path.abspath (__file__)), "methods.json")) as f:
    methods = json.load (f)

app = tk.Tk ()
app.title ("Diacritik")
app.configure (padx = 10, pady = 10)

key_label = tk.Label (app, text = "Type a key:", font = ("Courier", 32), fg = "black")
key_label.pack ()
opt_label = tk.Label (app, text = "[ ]" * 10, font = ("Courier", 32), fg = "black")
opt_label.pack ()

selecting = False
def display_key (event):
    global selecting, key_map, app
    key = event.char
    if not key:
        return

    elif ord (key) == 27: # Escape
        if selecting:
            selecting = False
            opt_label.config (text = "[ ]" * 10)
            key_label.config (text = "Type a key:", fg = "black")
        else:
            app.destroy ()
        return
    elif ord (key) == 13: # Enter
        if selecting:
            app.destroy ()
        return
    elif ord (key) < 32 or ord (key) > 126:
        return # Ignore non-printable characters

    if selecting and event.char in "1234567890" [ : len (key_map [selecting])]:
        selecting = key_map [selecting] ["1234567890".index (event.char)]
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

app.bind ("<Key>", display_key)
app.mainloop ()

if not selecting:
    raise SystemExit
sel_hex = format (ord (selecting), "04x")

focused = subprocess.run (methods ["__cmd__"], capture_output = True, shell = True)
focused.check_returncode ()
focused = focused.stdout.decode ().strip ()
method = methods.get (focused, methods ["__default__"])

if method == "char":
    os.system (f"wtype {selecting}")
elif method == "hex":
    subprocess.run ("wtype -M ctrl -M shift -k U -k {} -k {} -k {} -k {} -k Return".format (*sel_hex).split ()).check_returncode ()
