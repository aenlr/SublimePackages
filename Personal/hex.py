import sublime
import sublime_plugin

import re

from .common import EncodingInputHandler


def decode_hex_string(h: str) -> bytes:
    h = re.sub("&#([0-9a-fA-F]{1,2});", lambda m: m[1].rjust(2, "0"), h)
    h = re.sub("0[xXh]([0-9a-fA-F]{1,2})", lambda m: m[1].rjust(2, "0"), h)
    p = re.compile("^[^a-fA-F0-9]+")
    h = "".join(map(lambda l: p.sub("", l), h.splitlines()))
    h = re.sub(r"[^0-9a-fA-F]", "", h)
    if len(h) % 2:
        h = "0" + h
    return bytes.fromhex(h)


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

        if ch == "\t":
            pos += tab_size - (pos % tab_size)

        elif ch.isspace():
            pos += 1

        # elif non_space:
        #     break
        else:
            pos += 1

    return pos


class HexDecodeCommand(sublime_plugin.TextCommand):
    def input(self, args: dict):
        if "encoding" not in args:
            return EncodingInputHandler()
        return None

    def run(self, edit, encoding):
        regions = [s for s in self.view.sel()]
        tab_size = int(self.view.settings().get("tab_size", 8))
        insert_spaces = self.view.settings().get("translate_tabs_to_spaces", False)

        change_id = self.view.change_id()
        for r in regions:
            r = self.view.transform_region_from(r, change_id)
            text = self.view.substr(r).strip()
            if text:
                if text[0] in ('"', "'") and text[-1] == text[0]:
                    quote = text[0]
                    text = text[1:-1]
                else:
                    quote = ""
                text = (
                    quote
                    + decode_hex_string(text).decode(encoding, errors="replace")
                    + quote
                )
                indent = normed_indentation_pt(self.view, r, tab_size)
                if indent:
                    if insert_spaces:
                        text = text.replace(
                            "\n", "\n" + " " * (tab_size * int(indent / tab_size))
                        )
                    else:
                        text = text.replace("\n", "\n" + "\t" * int(indent / tab_size))
                self.view.replace(edit, r, text)
