import argparse
import glob
from typing import AnyStr
from readoc_parser import *
from readoc import ReaDoc
from bs4 import BeautifulSoup

ultraschall_path: str = 'YOUR/PATH/TO/ULTRASCHALL_API/FOLDER/'

arg_parser = argparse.ArgumentParser(description='ReaScriptDocParser')
arg_parser.add_argument('-p','--parser',
                        dest='parser',
                        help='Parser used (possible values: "vsc", "raw"), default:vsc',
                        metavar='{vsc|raw}',
                        default='vsc',
                        required=False)
arg_parser.add_argument('-pa','--parse-all',
                        dest='parse_all',
                        help='Parse all files, default True (become false if one other parse is enable)',
                        action='store_true',
                        default=True,
                        required=False)
arg_parser.add_argument('-r','--rebuild-usdoc',
                        dest='rebuild_usdoc',
                        help='Rebuild ultraschall.USDocML (path is optional if ultraschall_path is set)',
                        nargs='?',
                        const=ultraschall_path,
                        metavar='PATH/TO/ULTRASCHALL_API/',
                        default='',
                        required=False)
arg_parser.add_argument('-ro','--rebuild-usdoc-only',
                        dest='rebuild_usdoc_only',
                        help='Rebuild ultraschall.USDocML, exit program after  (path is optional if ultraschall_path is set)',
                        nargs='?',
                        const=ultraschall_path,
                        metavar='PATH/TO/ULTRASCHALL_API/',
                        default='',
                        required=False)
arg_parser.add_argument('-pr','--parse-reaper',
                        dest='parse_reaper',
                        help='Parse reaper documentation',
                        action='store_true',
                        default=False,
                        required=False)
arg_parser.add_argument('-pru','--parse-reaper-usdoc',
                        dest='parse_reaper_usdoc',
                        help='Parse reaper USDocML documentation',
                        action='store_true',
                        default=False,
                        required=False)
arg_parser.add_argument('-pvp','--parse-video-processor',
                        dest='parse_video_processor',
                        help='Parse video processor documentation',
                        action='store_true',
                        default=False,
                        required=False)
arg_parser.add_argument('-pus','--parse-ultraschall',
                        dest='parse_ultraschall',
                        help='Parse ultraschall documentation',
                        action='store_true',
                        default=False,
                        required=False)
arg_parser.add_argument('-pra','--parse-reaper-action',
                        dest='parse_reaper_action',
                        help='Parse reaper action list',
                        action='store_true',
                        default=False,
                        required=False)
arg_parser.add_argument('-psa','--parse-sws-action',
                        dest='parse_sws_action',
                        help='Parse sws action list',
                        action='store_true',
                        default=False,
                        required=False)

args = arg_parser.parse_args()

if True in [args.parse_reaper,args.parse_reaper_usdoc,args.parse_video_processor,
            args.parse_ultraschall,args.parse_reaper_action,args.parse_sws_action]:
    args.parse_all = False
if args.parse_all:
    args.parse_reaper = args.parse_reaper_usdoc = args.parse_video_processor = \
    args.parse_ultraschall = args.parse_reaper_action = args.parse_sws_action = True


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
        if re.search(r"_beta\.lua$", file) is not None:
            continue
        with open(file, 'r', encoding='utf8', errors='replace') as f:
            data = f.read()
            regex: str = r"function ultraschall\..*?\(.*?\)[\s\n]*--\[\[[\s\n]*(<US_DocBloc(?:.|\n)*?/US_DocBloc>)"
            for m in re.finditer(regex, data):
                us_file.write('\n' + m.group(1) + '\n')
    us_file.close()


if __name__ == "__main__":

    # --- INPUTS-OUPUTS ARGUMENTS / PARSER CONFIG ---

    # pretty = readable but large file, not-pretty = opposite
    # opti_lang = if a keyword is available in all languages, don't put any scope, reduce overall size
    vsc_parser_config: dict = dict({'pretty': True, 'opti_lang': True})

    us_output_path: str = 'api/ultraschall.USDocML'

    output_dir: str = 'raw/'
    output_format: str = '.txt'
    if args.parser == 'vsc':
        output_dir = 'vscode_snippets/'
        output_format: str = '.code-snippets'

    inputs_outputs: dict = dict({
        "api/reascripthelp.html": "reascript" if args.parse_reaper else None,
        "api/reaper-videoprocessor-docs.USDocML": "reascript_vp" if args.parse_video_processor else None,
        "api/reaper-apidocs.USDocML": "reascript_usdoc" if args.parse_reaper_usdoc else None,
        "api/ultraschall.USDocML": "ultraschall" if args.parse_ultraschall else None,
        "api/reaper_ActionList.txt": "reaper_action_list" if args.parse_reaper_action else None,
        "api/sws_ActionList.txt": "sws_action_list" if args.parse_sws_action else None
    })

    # ---

    if args.rebuild_usdoc != '' or args.rebuild_usdoc_only != '':
        print("Building {} ...".format(us_output_path))
        build_usdoc(args.rebuild_usdoc_only if args.rebuild_usdoc_only != '' else args.rebuild_usdoc, us_output_path)
        print("Build of {} done !".format(us_output_path))
        if args.rebuild_usdoc_only != '':
            exit(0)

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

        if args.parser == 'vsc':
            doc_parser = VscParser(readoc, **vsc_parser_config)
        else:
            doc_parser = RawParser(readoc)

        doc_parser.export(output)

        print("Build of {} done !".format(output))

    exit(0)
