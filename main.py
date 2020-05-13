from typing import AnyStr
from readoc_parser import *
from readoc import ReaDoc
from bs4 import BeautifulSoup

if __name__ == "__main__":

    api_doc: str = "api/reascripthelp.html"
    output: str = "snippets/reascript"
    vsc_parser_config: dict = dict({'pretty': True})  # pretty = readable but large file, not-pretty = opposite
    parser: str = 'vsc'  # Valid parser : 'vsc', anything else take raw parser

    html_doc: AnyStr = open(api_doc, 'r').read()
    soup: BeautifulSoup = BeautifulSoup(html_doc, features="html.parser")
    readoc: ReaDoc = ReaDoc(soup)

    if parser == 'vsc':
        output += ".code-snippets"
        doc_parser = VscParser(readoc, **vsc_parser_config)
    else:
        output += ".txt"
        doc_parser = RawParser(readoc)
    doc_parser.export(output)
