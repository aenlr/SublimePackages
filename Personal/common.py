import sublime_plugin


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
