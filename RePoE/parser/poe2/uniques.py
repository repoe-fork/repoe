import re
from html import escape
from urllib.parse import quote

from RePoE.parser import Parser_Module
from RePoE.parser.util import call_with_default_args, export_image, write_json, write_text, compose_flask


class uniques(Parser_Module):
    def write(self) -> None:
        root = {}

        ddsfiles = {}
        for visuals in self.relational_reader["ItemVisualIdentity.dat64"]:
            if re.search('unique', visuals["DDSFile"], re.IGNORECASE):
                ddsfiles[visuals["DDSFile"]] = visuals["Composition"]

        names = set()
        for word in self.relational_reader["Words.dat64"]:
            if word["Wordlist"] == 6:
                names.add(word["Text2"])

        html = (
                """<!DOCTYPE html>
    <html>
    <head>
     <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
     <title>"""
                + escape(
            self.relational_reader["ClientStrings.dat64"].index["Id"]["TutorialPanelRarityTiersSubtitle1"]["Text"]
        )
                + """</title>
 <style type="text/css">
  BODY { font-family : monospace, sans-serif;  color: black;}
  A:visited { text-decoration : none; margin : 0px; padding : 0px;}
  A:link    { text-decoration : none; margin : 0px; padding : 0px;}
  A:hover   { text-decoration: underline; background-color : yellow; margin : 0px; padding : 0px;}
  A:active  { margin : 0px; padding : 0px;}
 </style>
</head>
<body>""")
        if self.language == "English":
            html = (html + """
    <h1>
        Unique Item Art
    </h1>
    <p>
        Item drop rates cannot be found in the game files, thus we cannot confirm if uniques listed on this page are
        actually available in-game.
    </p>
    <h2>
        Unique stash tab contents
    </h2>""")

        stash_type = ""
        for item in sorted(self.relational_reader["UniqueStashLayout.dat64"],
                           key=lambda i: (i["UniqueStashTypesKey"]["Name"], i["WordsKey"]["Text2"])):
            name = item["WordsKey"]["Text2"]
            names.discard(name)
            root[str(item.rowid)] = {
                "id": item["WordsKey"]["Text"],
                "name": name,
                "item_class": item["UniqueStashTypesKey"]["Id"],
                "inventory_width": item[5] or item["UniqueStashTypesKey"]["Width"],
                "inventory_height": item[6] or item["UniqueStashTypesKey"]["Height"],
                "is_alternate_art": item["IsAlternateArt"],
                "renamed_version": item["RenamedVersion"]
                                   and {
                                       "rowid": item["RenamedVersion"].rowid,
                                       "name": item["RenamedVersion"]["WordsKey"]["Text2"],
                                   },
                "base_version": item["BaseVersion"]
                                and {"rowid": item["BaseVersion"].rowid,
                                     "name": item["BaseVersion"]["WordsKey"]["Text2"]},
                "visual_identity": {
                    "id": item["ItemVisualIdentityKey"]["Id"],
                    "dds_file": item["ItemVisualIdentityKey"]["DDSFile"],
                },
            }

            if item["ItemVisualIdentityKey"]["DDSFile"]:
                if stash_type != item["UniqueStashTypesKey"]["Name"]:
                    stash_type = item["UniqueStashTypesKey"]["Name"]
                    html = html + f"\n\t<h3>{escape(stash_type)}</h3>"
                ddsfile: str = item["ItemVisualIdentityKey"]["DDSFile"]
                ddsfiles.pop(ddsfile, None)
                composition = item["ItemVisualIdentityKey"]["Composition"]
                name = escape(name) + (" (Alternate Art)" if item["IsAlternateArt"] else "")
                href = ("" if self.language == "English" else "../") + ddsfile.replace(".dds", ".png")
                html = html + f"\n\t<a href='{quote(href)}'>{name}</a><br>"
                if self.language == "English":
                    export_image(ddsfile, self.data_path, self.file_system,
                                 compose=compose_flask if composition == 1 else None)

        if self.language == "English":
            html = (
                    html
                    + """
    <h2>
        Other item art with 'unique' in the file name:
    </h2>""")
            for ddsfile, composition in sorted(ddsfiles.items()):
                try:
                    self.file_system.index.get_file_record(ddsfile)
                    if self.language == "English":
                        export_image(ddsfile, self.data_path, self.file_system,
                                     compose=compose_flask if composition == 1 else None)
                    href = ddsfile.replace(".dds", ".png")
                    html = html + f"\n\t<img src='{quote(href)}' />"
                except FileNotFoundError:
                    pass
            html = (
                    html
                    + """
    <h2>
        Possible unique names not listed above:
    </h2>""")
            for name in sorted(names):
                html = html + f"\n\t{escape(name)}<br>"

        html = (html + """
</body>
</html>
""")

        write_json(root, self.data_path, "uniques")
        write_text(html, self.data_path, "uniques.html")


if __name__ == "__main__":
    call_with_default_args(uniques, True)
