from typing import AnyStr
from readoc_parser import *
from readoc import ReaDoc
from bs4 import BeautifulSoup
import glob


def build_usdoc(us_path: str, output_file: str):
    """Build a USDocML file for Ultraschall

    :param us_path: Path of Ultraschall folder (put '/' at the end)
    :param output_file: Output USDocML path + file name
    """
    # Clear output file
    us_file = open(output_file, "w")
    us_file.write('')
    us_file.close()

    us_file = open(output_file, "a")
    for file in glob.iglob(us_path + '/**/*.lua', recursive=True):
        with open(file, 'r', encoding='utf8', errors='replace') as f:
            data = f.read()
            regex: str = r"function ultraschall\..*?\(.*?\)[\s\n]*--\[\[[\s\n]*(<US_DocBloc(?:.|\n)*?/US_DocBloc>)"
            for m in re.finditer(regex, data):
                us_file.write('\n' + m.group(1) + '\n')
    us_file.close()


if __name__ == "__main__":

    build_us_doc: bool = False
    if build_us_doc:
        us_path: str = 'YOUR/PATH/TO/ULTRASCHALL/API/FOLDER/'
        us_output_path: str = 'api/ultraschall.USDocML'
        build_usdoc(us_path,us_output_path)
        exit(0)

    parser: str = 'vsc'  # Valid parser : 'vsc', anything else take raw parser

    # pretty = readable but large file, not-pretty = opposite
    # opti_lang = if a keyword is available in all languages, don't put any scope, reduce overall size
    vsc_parser_config: dict = dict({'pretty': True, 'opti_lang': True})

    output_dir: str = 'raw/'
    output_format: str = '.txt'
    if parser == 'vsc':
        output_dir = 'vscode_snippets/'
        output_format: str = '.code-snippets'
    inputs_outputs: dict = dict({
        "api/reascripthelp.html": "reascript",
        "api/reaper-videoprocessor-docs.USDocML": "reascript_vp",
        "api/reaper-apidocs.USDocML": "reascript_usdoc",
        "api/ultraschall.USDocML": "ultraschall",
        "api/reaper_ActionList.txt": "reaper_action_list",
        "api/sws_ActionList.txt": "sws_action_list"
        })

    for api_doc, output in inputs_outputs.items():
        if output is None:
            continue
        output = output_dir + output + output_format
        print("Converting {} to {} ...".format(api_doc, output))
        doc_format: str = api_doc.rsplit('.')[-1]
        with open(api_doc, 'r') as f:
            doc_data: AnyStr = f.read()

        soup: BeautifulSoup = BeautifulSoup(doc_data, features="html.parser")
        readoc: ReaDoc = ReaDoc(soup, doc_format)

        if parser == 'vsc':
            doc_parser = VscParser(readoc, **vsc_parser_config)
        else:
            doc_parser = RawParser(readoc)

        doc_parser.export(output)

        print("Build of {} done !".format(output))

    exit(0)
