import sublime
import sublime_plugin

import base64
import json


def pretty_dumps(v) -> str:
    return json.dumps(v, indent=2, ensure_ascii=False)


def pretty_print(text: str) -> str:
    if not (text.startswith("{") or text.startswith("[")):
        return text

    v = json.loads(text)
    return pretty_dumps(v)


def base64_decode_urlsafe(text: str) -> bytes:
    b = text.encode("ascii")
    missing_padding = len(b) % 4
    if missing_padding and not b.endswith(b"="):
        b += b"=" * (4 - missing_padding)
    return base64.urlsafe_b64decode(b)


def decode_jwt(text: str) -> tuple:
    parts = text.split('.', 2)
    header = json.loads(base64_decode_urlsafe(parts[0]))
    if len(parts) == 1:
        jws = header
    else:
        jws = {"protected": header}

        if "b64" in header and not header["b64"]:
            payload = parts[1]
            if payload.startswith("{"):
                payload = json.loads(payload)
        else:
            payload = json.loads(base64_decode_urlsafe(parts[1]))
        jws["payload"] = payload
        if len(parts) == 3:
            jws["signature"] = parts[2]

    return jws


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


class JwtDecodeCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        regions = [s for s in self.view.sel()]
        tab_size = int(self.view.settings().get('tab_size', 8))
        json_indent = tab_size
        insert_spaces = self.view.settings().get('translate_tabs_to_spaces', False)
        syntax = self.view.syntax()
        convert_to_json = self.view.buffer().file_name() is None and (syntax is None or syntax.name == 'Plain Text')
        if convert_to_json:
            insert_spaces = True
            json_indent = 2

        change_id = self.view.change_id()
        for r in regions:
            r = self.view.transform_region_from(r, change_id)
            text = self.view.substr(r).strip()
            if text:
                jws = decode_jwt(text)
                indent = normed_indentation_pt(self.view, r, tab_size)
                text = json.dumps(jws, indent=json_indent if insert_spaces else '\t', ensure_ascii=False)
                if indent:
                    if insert_spaces:
                        text = text.replace("\n", "\n" + " " * (tab_size * int(indent / tab_size)))
                    else:
                        text = text.replace("\n", "\n" + "\t" * int(indent / tab_size))
                self.view.replace(edit, r, text)

        if convert_to_json:
            self.view.assign_syntax('Packages/JavaScript/JSON.sublime-syntax')
