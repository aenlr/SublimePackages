import sublime
import sublime_plugin

import base64
import json


def base64_decode_urlsafe(text: str, encoding="utf-8") -> str:
    try:
        b = text.encode("ascii")
    except:
        return text
    missing_padding = len(b) % 4
    if missing_padding: # and not b.endswith(b"="):
        b += b"=" * (4 - missing_padding)
    b = base64.urlsafe_b64decode(b)
    try:
        if encoding == "utf-8":
            return b.decode(encoding)
        else:
            return b.decode(encoding, errors='replace')
    except:
        print("Falling back to iso-8859-1")
        return b.decode("iso-8859-1")


def base64_encode_urlsafe(text: str, encoding="utf-8", padding=False) -> str:
    b = text.encode(encoding)
    encoded = base64.urlsafe_b64encode(b)
    if not padding:
        encoded = encoded.rstrip(b"=")
    return encoded.decode("ascii")


def base64_encode(text: str, encoding="utf-8", padding=False) -> str:
    b = text.encode(encoding)
    encoded = base64.b64encode(b)
    if not padding:
        encoded = encoded.rstrip(b"=")
    return encoded.decode("ascii")


def normed_indentation_pt(view, sel, tab_size):
    """
    Calculates tab normed `visual` position of sel.begin() relative "
    to start of line

    \n\t\t\t    => normed_indentation_pt => 12
    \n  \t\t\t  => normed_indentation_pt => 12

    Different amount of characters, same visual indentation.
    """

    pos = 0
    ln = view.line(sel)

    for pt in range(ln.begin(), sel.begin()):
        ch = view.substr(pt)

        if ch == '\t':
            pos += tab_size - (pos % tab_size)

        elif ch.isspace():
            pos += 1

        # elif non_space:
        #     break
        else:
            pos += 1

    return pos


class EncodingInputHandler(sublime_plugin.ListInputHandler):
    def name(self):
        return "encoding"

    def list_items(self):
        return [
            ("UTF-8", "utf-8"),
            ("Latin 1", "iso-8859-1"),
            ("Windows 1252", "cp1252"),
            ("ISO 8859-15", "iso-8859-15"),
            ("ASCII", "ascii"),
        ]



class Base64DecodeCommand(sublime_plugin.TextCommand):
    def input(self, args: dict):
        if "encoding" not in args:
            return EncodingInputHandler()
        return None

    def run(self, edit, encoding):
        regions = [s for s in self.view.sel()]
        tab_size = int(self.view.settings().get('tab_size', 8))
        insert_spaces = self.view.settings().get('translate_tabs_to_spaces', False)

        change_id = self.view.change_id()
        for r in regions:
            r = self.view.transform_region_from(r, change_id)
            text = self.view.substr(r).strip()
            if text:
                text = base64_decode_urlsafe(text, encoding)
                indent = normed_indentation_pt(self.view, r, tab_size)
                if indent:
                    if insert_spaces:
                        text = text.replace("\n", "\n" + " " * (tab_size * int(indent / tab_size)))
                    else:
                        text = text.replace("\n", "\n" + "\t" * int(indent / tab_size))
                self.view.replace(edit, r, text)


class Base64EncodeCommand(sublime_plugin.TextCommand):
    def input(self, args: dict):
        if "encoding" not in args:
            return EncodingInputHandler()
        return None

    def run(self, edit, encoding="utf-8", url=False, padding=None):
        regions = [s for s in self.view.sel()]
        change_id = self.view.change_id()
        for r in regions:
            r = self.view.transform_region_from(r, change_id)
            text = self.view.substr(r).strip()
            if text:
                if url:
                    text = base64_encode_urlsafe(text, encoding, padding)
                else:
                    text = base64_encode(text, encoding, padding)
                self.view.replace(edit, r, text)

