from bs4 import BeautifulSoup, NavigableString
from typing import List, Tuple, Dict, Optional
import re

languages: dict = dict({'C: ': 'c', 'EEL: ': 'eel2', 'Lua: ': 'lua', 'Python: ': 'python'})


class FunctionDoc:
    """
        Intermediate representation of a function.
    """

    def __init__(self, code: str, desc: str, lang: str):
        self.desc: str = desc
        self.lang = lang
        code = code.replace('{', '').replace('}', '').replace(']', '').replace('[', '') \
            .replace('reaper.array', 'reaper_array').replace('\n', '')

        match = re.search("(?:(.*)\s=?\s?)?(.*?)\((.*)\)", code)
        self.name: str = match.group(2)

        # Pair is (type,name)
        self.returns: List[Tuple[str, str]] = []
        returns_text = match.group(1) if match.group(1) is not None else ''
        returns_text = returns_text.replace(', ', ',').replace('(', '').replace(')', '').replace(' =', '')
        if returns_text != '':
            for x in returns_text.split(','):
                self.returns.append((x.rsplit(' ', 1)[0], x.rsplit(' ', 1)[1] if len(x.split(' ')) > 1 else ''))

        # Pair is (type,name)
        self.params: List[Tuple[str, str]] = []
        if match.group(3) != '':
            for x in match.group(3).replace(', ', ',').replace('(', '').replace(')', '').split(','):
                self.params.append((x.rsplit(' ', 1)[0], x.rsplit(' ', 1)[1] if len(x.split(' ')) > 1 else ''))

        # Key : parameter name, value : possible values (for now only for parmname, desc parameter)
        self.options: Dict[str, List[str]] = dict()


class KeywordDoc:
    """
        Intermediate representation of a keyword.
        Keywords are words like 'parmname' in Info_Value / Info_String functions or gfx attributes
    """

    def __init__(self, name: str, desc: str, langs: Optional[List[str]] = None):
        self.name: str = name
        self.desc: str = desc
        if langs is None:
            langs: List[str] = []
            for key, lang in languages.items():
                langs.append(lang)
        self.languages = langs


class ReaDoc:
    """
        Intermediate representation of the Reascript documentation.
        Current extracted data are:
        - Functions with their name, description, language, parameters (type, names and possible values) and return values (type and names)
        - Keywords detected in functions' descriptions (e.g. gfx variables, 'parmname' possible values) along with their own description and their language.
    """

    def __init__(self, soup: BeautifulSoup):
        self.functions: List[FunctionDoc] = []
        self.keywords: Dict[str, KeywordDoc] = dict()  # Key : keyword name

        for hr in soup.find_all('hr'):
            function_code: Dict[str, str] = dict()  # Key = language, value = code
            new_keywords: List[str] = []
            current_lang: str = 'unknow'
            desc: str = ''
            div_parent = hr.parent
            update_gfx: bool = False
            if div_parent.name != 'a' or 'name' not in div_parent.attrs.keys():
                # Not a function definition
                continue
            for sibling in div_parent.next_siblings:
                if (sibling.name == 'a' and 'href' not in sibling.attrs.keys()) \
                        or (sibling.name == 'a' and 'name' in sibling.attrs.keys()) \
                        or sibling.name == 'hr' \
                        or (sibling.name == 'div' and desc != ''):
                    # End of the function definition reached
                    if update_gfx:
                        self.update_gfx(desc, current_lang)
                    break
                elif type(sibling) is NavigableString and sibling.string == '\n':
                    # Ignore
                    continue
                elif sibling.name == 'br':
                    if desc != '':
                        desc += "\n"
                    continue

                if type(sibling) is NavigableString and sibling.string.replace('\n', '') in languages.keys():
                    # Some function don't have language in a 'span' tag
                    # It will be a NavigableString (e.g '\nEEL: ')
                    current_lang = languages[sibling.string.replace('\n', '')]
                    continue
                elif type(sibling) is NavigableString:
                    desc += sibling.string
                    continue
                elif sibling.name in ['a', 'i', 'table', 'li']:
                    # Descriptions can have those tags in them
                    desc += sibling.text
                    continue
                elif sibling.name in ['ul']:
                    # Descriptions can have ul tag in them
                    for content in sibling.contents:
                        if type(content) is not NavigableString:
                            desc += '\n>> ' + content.text.replace('\n', '')
                    continue

                if sibling.find('span') is not None and sibling.find('span').text in languages.keys():
                    current_lang = languages[sibling.find('span').text]

                if sibling.find('code') is not None or sibling.name == 'code':
                    code_text: str = ''
                    if sibling.name == 'code':
                        if sibling.text == 'gfx VARIABLES':
                            update_gfx = True
                            continue
                        elif sibling.previous_sibling.string[1:] in languages.keys():
                            code_text = sibling.text
                        else:
                            # Description can contains code
                            desc += sibling.text
                            continue
                    else:
                        code_text = sibling.find('code').text
                    if code_text == "reaper.get_action_context()":
                        # Code of this function doesnt have return values
                        code_text = "is_new_value,filename,sectionID,cmdID,mode,resolution,val = reaper.get_action_context()"
                    function_code[current_lang] = code_text

            for lang, code in function_code.items():
                if len(desc) > 1 and desc[0] == '\n':
                    desc = desc[1:]
                new_function = FunctionDoc(code, desc.replace('\n\n', '\n'), lang)
                self.functions.append(new_function)
                new_keywords = self.update_keywords(desc, lang)

                if len(new_keywords) > 0:
                    for param_name in ['parmname', 'desc']:
                        for param in new_function.params:
                            if len(param) > 1 and param_name == param[1]:
                                new_function.options[param_name] = new_keywords

    def update_keywords(self, desc: str, lang: str) -> List[str]:
        """Update keywords attributes

        :param desc: Description of the function
        :param lang: Language
        :return: List of all founded keywords
        """

        searched_keywords: str = "I_|P_|B_|C_|D_|F_|IP_|MARKER_|RECORD_|RENDER_|GUID"
        regex_keywords: str = "((?:" + searched_keywords + ")[^\s]*?)\s?:\s?"
        found_keywords: List[str] = []
        for m in re.finditer(regex_keywords, desc):
            keyword: str = m.group(1)
            found_keywords.append(keyword)
            keyword_desc = desc[m.span()[1]:]

            if re.search('\n\n', keyword_desc) is not None and re.search('\n\n', keyword_desc).end() != len(
                    keyword_desc):
                keyword_desc = keyword_desc[:re.search('\n\n', keyword_desc).start()]
            elif re.search("[^\sA-Z](" + searched_keywords + ")", keyword_desc) is not None:
                # Some description don't have \s or anything between keywords definition
                # A-Z : avoid taking false positive keywords like 'C_MAINSEND_OFFS'
                keyword_desc = keyword_desc[:re.search("[^\sA-Z](" + searched_keywords + ")", keyword_desc).start()]
            keyword_desc = keyword_desc.replace('\n', ' ')

            if keyword in self.keywords.keys():
                # Update the keyword
                if keyword_desc not in self.keywords[keyword].desc:
                    self.keywords[keyword].desc += ' / ' + keyword_desc
                if lang not in self.keywords[keyword].languages:
                    self.keywords[keyword].languages.append(lang)
            else:
                self.keywords[keyword] = KeywordDoc(keyword, keyword_desc)
        return found_keywords

    def update_gfx(self, desc: str, lang: str):
        """Update keywords attributes with gfx VARIABLES description

        :param desc: Description of gfx VARIABLES
        :param lang: Language
        """
        regex_keywords = "(gfx(:?_|.)[^,\s/.\(]*)"
        desc = desc.replace('gfx.mouse_cap', 'gfx.mouse_cap - ')  # Small fix
        for m in re.finditer(regex_keywords, desc):
            keyword = m.group(1)
            if re.search('-', desc[m.span()[1]:]) is None:
                break
            else:
                start_pos = m.span()[1] + re.search('-', desc[m.span()[1]:]).start() + 2
            end_pos = re.search('>>', desc[start_pos:])
            if end_pos is None:
                self.keywords[keyword] = KeywordDoc(keyword, desc[start_pos:], [lang])
            else:
                self.keywords[keyword] = KeywordDoc(keyword, desc[start_pos:start_pos + end_pos.start()], [lang])
