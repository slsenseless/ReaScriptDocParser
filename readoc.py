from bs4 import BeautifulSoup, NavigableString
from typing import List, Tuple, Dict, Optional, Union
import re

languages: dict = dict({'C: ': 'c', 'EEL: ': 'eel2', 'Lua: ': 'lua', 'Python: ': 'python'})


class VariableDoc:
    """
        Intermediate representation of a variable (function parameter or return)
    """

    def __init__(self, type: str, name: str = '', desc: str = ''):
        """
            Type can be its name if the variable doesnt have a type !
        """
        self.type: str = type
        self.name: str = name
        self.desc: str = desc
        self.values: List[str] = []  # Possible values for parameter


class FunctionDoc:
    """
        Intermediate representation of a function.
    """

    def __init__(self, code: str, desc: str, lang: str):
        self.desc: str = FunctionDoc.trim_desc(desc)
        self.lang = lang
        code = code.replace('{', '').replace('}', '').replace(']', '').replace('[', '') \
            .replace('reaper.array', 'reaper_array').replace('\n', '')

        match = re.search("(?:(.[^(]*)\s=?\s?)?(.[^(]*?)\((.*)\)", code)
        self.name: str = match.group(2)

        # Pair is (type,name)
        self.returns: List[VariableDoc] = []
        returns_text = match.group(1) if match.group(1) is not None else ''
        returns_text = returns_text.replace(', ', ',').replace('(', '').replace(')', '').replace(' =', '')
        if returns_text != '':
            for x in returns_text.split(','):
                self.returns.append(VariableDoc(x.rsplit(' ', 1)[0], x.rsplit(' ', 1)[1] if len(x.split(' ')) > 1 else ''))

        # Pair is (type,name)
        self.params: List[VariableDoc] = []
        if match.group(3) != '':
            for x in match.group(3).replace(', ', ',').replace('(', '').replace(')', '').split(','):
                self.params.append(VariableDoc(x.rsplit(' ', 1)[0], x.rsplit(' ', 1)[1] if len(x.split(' ')) > 1 else ''))

    def update_params_values(self, values:List[str]):
        if len(values) > 0:
            for param_name in ['parmname', 'desc']:
                for param in self.params:
                    if param.name == param_name:
                        param.values = values

    @staticmethod
    def trim_desc(desc: str) -> str:
        """Trim desc : remove useless whitespace

        :param desc: Description to trim
        :return: Trimed description
        """
        clear_desc: str = desc
        clear_desc = re.sub(r"[\n\s]*$", "", clear_desc)
        clear_desc = re.sub(r"^[\n\s]*", "", clear_desc)
        clear_desc = re.sub(r"\s*\n\s*", "\n", clear_desc)
        return clear_desc

    def get_full_desc(self) -> str:
        """Return the description along with parameters and returns descriptions

        :return: The full description
        """
        desc: str = self.desc
        if self.has_desc(self.params):
            desc += '\nPARAMETERS:'
            for param in self.params:
                desc += '\n'+ param.name + ':' + param.desc if param.desc != '' else ''
        if self.has_desc(self.returns):
            desc += '\nRETURNS:'
            for ret in self.returns:
                ret_name = ret.name if ret.name != '' else ret.type
                desc += '\n'+ ret_name + ':' + ret.desc if ret.desc != '' else ''
        return desc

    def has_desc(self, vars: List[VariableDoc]) -> bool:
        for var in vars:
            if var.desc != '':
                return True
        return False


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


class AliasDoc:

    def __init__(self, alias: str, name: str, desc: str):
        self.alias = alias
        self.name = name
        self.desc = desc


class ReaDoc:
    """
        Intermediate representation of the Reascript documentation.
        Current extracted data are:
        - Functions with their name, description, language, parameters (type, names and possible values) and return values (type and names)
        - Keywords detected in functions' descriptions (e.g. gfx variables, 'parmname' possible values) along with their own description and their language.
    """

    def __init__(self, soup: BeautifulSoup, format: str = 'html'):
        """ Extract documentation information

        :param soup: BeautifulSoup object of the file
        :param format: file type (Possible values: 'html','USDocML')
        """
        self.functions: List[FunctionDoc] = []
        self.keywords: Dict[str, KeywordDoc] = dict()  # Key : keyword name
        self.aliases: Dict[AliasDoc] = dict()  # Key : alias

        if format == 'html':
            self.extract_html(soup)
        elif format == 'USDocML':
            self.extract_usdoc(soup)
        elif format == 'txt':
            self.extract_txt(soup)

    def extract_usdoc(self, soup: BeautifulSoup):
        for func_bloc in soup.find_all('us_docbloc'):
            function_calls = func_bloc.findChildren('functioncall')
            if len(function_calls) == 0:
                continue
            desc: str = func_bloc.find('description').text
            for func in function_calls:
                lang: str = func['prog_lang'] if 'prog_lang' in func.attrs.keys() else 'lua'
                new_keywords: List[str] = self.update_keywords(desc, lang)
                desc = re.sub('\[(.*)\]\(#.*\)', '\g<1>', desc)  # Replace link by plain text
                if func.text == 'gfx VARIABLES':
                    self.update_gfx(desc,lang)
                elif func.text.find('(') == -1:
                    # Is actually a keyword (possible in videoprocessor doc)
                    self.keywords[func.text] = KeywordDoc(func.text,FunctionDoc.trim_desc(desc),[lang])
                    pass
                else:
                    new_function = FunctionDoc(func.text,desc,lang)
                    self.functions.append(new_function)
                    new_function.update_params_values(new_keywords)
                    self.update_var_desc(func_bloc,new_function.returns,'retvals')
                    self.update_var_desc(func_bloc,new_function.params,'parameters')

    def update_var_desc(self, func_bloc, variables: List[VariableDoc], tag_name:str):
        child = func_bloc.findChild(tag_name)
        if child is not None:
            for m in re.finditer(r"(.*?)\s-\s(.*)", child.text):
                for var in variables:
                    if var.name in m.group(1):
                        var.desc = re.sub('\[(.*)\]\(#.*\)', '\g<1>', m.group(2))

    def extract_html(self, soup: BeautifulSoup):
        for hr in soup.find_all('hr'):
            function_code: Dict[str, str] = dict()  # Key = language, value = code
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
                new_function = FunctionDoc(code, desc.replace('\n\n', '\n'), lang)
                self.functions.append(new_function)
                new_keywords: List[str] = self.update_keywords(desc, lang)
                new_function.update_params_values(new_keywords)

    def update_keywords(self, desc: str, lang: str) -> List[str]:
        """Update keywords attributes

        :param desc: Description of the function
        :param lang: Language
        :return: List of all founded keywords
        """

        desc = desc.replace('\\','')  # In USDocML: can have 'I\_...'
        searched_keywords: str = r"I_|P_|B_|C_|D_|F_|IP_|MARKER_|RECORD_|RENDER_|PROJECT_|GUID"
        regex_keywords: str = "([^\sA-Z]?((?:" + searched_keywords + ")[^\s]*?)\n?\s?:\s)"
        found_keywords: List[str] = []
        matches: List = []
        for m in re.finditer(regex_keywords, desc):
            matches.append(m)
        for i, m in enumerate(matches):
            keyword: str = m.group(2)
            found_keywords.append(keyword)
            if m == matches[-1]:
                keyword_desc = desc[m.end(1):]
            else:
                keyword_desc = desc[m.end(1):matches[i+1].start(2)]

            if re.search('\n\n',keyword_desc) is not None:
                keyword_desc = keyword_desc[:re.search('\n\n',keyword_desc).start()]
            keyword_desc = re.sub(r"[\n\s]*$","",keyword_desc)
            keyword_desc = re.sub(r"^[\n\s]*","",keyword_desc)
            keyword_desc = re.sub(r"\n", " ", keyword_desc)

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
        regex_keywords = r"(gfx(:?_|.)[^,\s/.\(]*)"
        desc = desc.replace('gfx.mouse_cap', 'gfx.mouse_cap - ')  # Small fix
        for m in re.finditer(regex_keywords, desc):
            keyword = m.group(1)
            if 'init' in keyword:
                continue
            if re.search('-', desc[m.span()[1]:]) is None:
                break
            else:
                start_pos = m.span()[1] + re.search('-', desc[m.span()[1]:]).start() + 2
            end_pos = re.search('>>', desc[start_pos:])
            if end_pos is None:
                self.keywords[keyword] = KeywordDoc(keyword, desc[start_pos:], [lang])
            else:
                self.keywords[keyword] = KeywordDoc(keyword, desc[start_pos:start_pos + end_pos.start()], [lang])

    def extract_txt(self, soup: BeautifulSoup):
        for line in soup.contents[0].split('\n'):
            if line == '' or line.split('\t')[0] == 'Section':
                continue
            line = line.split('\t')
            alias_key: str = line[0] + "|" + line[1]
            desc: str = line[0] + "|" + line[2]
            alias: str = re.sub(r"[\s/]", '_', line[2])
            alias = re.sub(r"[^a-zA-Z0-9_+\-\<\>=\.]",'',alias)  # Remove every special character
            alias = line[0].replace(' ','_') + '_' + alias
            alias = alias.upper()
            # Some action are defined twice (we ignore them):
            # 41993/41994
            # 27288/27289
            # _S&M_..._Sl/_S&M_..._Sp
            if alias not in self.aliases.keys():
                self.aliases[alias] = AliasDoc(alias, line[1], desc)

            if line[1] not in self.keywords.keys():
                self.keywords[line[1]] = KeywordDoc(line[1], desc)
            else:
                self.keywords[line[1]].desc += '\n' + desc
