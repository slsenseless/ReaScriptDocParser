from typing import List, Tuple, Optional
import json
from abc import ABC, abstractmethod

from readoc import *


class ReaDocParser(ABC):
    """
        Parser abstract class, 'parse' method must be implemented.
    """

    def __init__(self, readoc: ReaDoc, **kwargs):
        self.output = self.parse(readoc, **kwargs)

    @abstractmethod
    def parse(self, readoc: ReaDoc, **kwargs) -> str:
        """
            Use to set the 'output' attribute, must implement in child class
        """
        pass

    def export(self, output_file: str):
        text_file = open(output_file, "w")
        text_file.write(self.output)
        text_file.close()


class VscParser(ReaDocParser):
    """
        VisualStudio Code Parser
    """

    def __init__(self, readoc: ReaDoc, **kwargs):
        super().__init__(readoc, **kwargs)

    def parse(self, readoc: ReaDoc, **kwargs) -> str:
        if kwargs is not None:
            if 'pretty' in kwargs:
                self.pretty = kwargs['pretty']
        doc: dict = dict()
        for func in readoc.functions:
            func_prop = self.get_function_dict(func)
            if func_prop is not None:
                doc[func.name.upper() + ' ' + func.lang] = func_prop

        for func in readoc.functions:
            func_prop = self.get_function_dict(func, True)
            if func_prop is not None:
                doc[func.name.upper() + '_WR ' + func.lang] = func_prop

        for key, keyword in readoc.keywords.items():
            for lang in keyword.languages:
                keyword_prop: dict = dict()
                keyword_prop['prefix'] = keyword.name
                keyword_prop['scope'] = lang
                keyword_prop['body'] = keyword.name
                keyword_prop['description'] = keyword.desc
                doc[keyword.name.upper() + ' ' + lang] = keyword_prop

        if self.pretty:
            return json.dumps(doc, indent=4, separators=(',', ': '))
        else:
            return json.dumps(doc)

    @staticmethod
    def get_function_dict(func: FunctionDoc, retval: bool = False) -> Optional[dict]:
        """Convert a FunctionDoc to a dict

        :param func: FunctionDoc to parse
        :param retval: True if 'with return' function, false otherwise
        :return: Function dict
        """
        if len(func.returns) == 0 and retval:  # Skip if useless
            return None

        func_prop: dict = dict()
        func_prop['prefix'] = func.name
        if func.lang == 'lua':
            func_prop['prefix'] = func.name.replace('reaper.', 'reaperwr.') if retval else func.name
        elif retval:
            func_prop['prefix'] = 'WR_' + func_prop['prefix']
        func_prop['scope'] = func.lang
        func_prop['description'] = func.desc
        body: str = ""
        i: int = 1
        if retval:
            if func.lang == 'lua':
                body += '${' + str(i) + ':local }'
                i += 1
            body_core, i = VscParser.get_body_core(func.returns, i)
            body += body_core
            body += ' = '

        body += func.name + '('
        body_core, i = VscParser.get_body_core(func.params, i)
        body += body_core
        body += ')$0'
        func_prop['body'] = body
        return func_prop

    @staticmethod
    def get_body_core(variables: List[VariableDoc], i: int) -> (str, int):
        body_core: str = ""
        for variable in variables:
            body_core += '${' + str(i)
            if len(variable.values) > 0:
                body_core += '|' + variable.type + (' ' + variable.name if variable.name != '' else '') + ','
                for value in variable.values:
                    body_core += '"' + value + '"' + ','
                body_core = body_core[:-1]  # Remove last comma
                body_core += '|'
            else:
                body_core += ':' + variable.type + (' ' + variable.name if variable.name != '' else '')

            body_core += '}'
            body_core += ',' if variable != variables[-1] else ''
            i += 1
        return body_core, i


class RawParser(ReaDocParser):
    """
        Raw parser
    """

    def __init__(self, readoc: ReaDoc, **kwargs):
        super().__init__(readoc, **kwargs)

    def parse(self, readoc: ReaDoc, **kwargs) -> str:
        output: str = "FUNCTIONS:\n"
        for func in readoc.functions:
            output += "name:" + func.name + "\n"
            output += "language:" + func.lang + "\n"

            output += "return:"
            for ret in func.returns:
                output += "(" + ret.type + ":" + ret.name + ")"
                output += "," if ret != func.returns[-1] else ""

            output += "\nparams:"
            for param in func.params:
                output += "(" + param.type + ":" + param.name + ")"
                output += ", " if param != func.params[-1] else ""

            for param in func.params:
                if len(param.values) > 0:
                    output += "\nValid input for " + param.name + ": "
                    for value in param.values:
                        output += value
                        output += ", " if value != param.values[-1] else ""
                    output += "\n"

            output += "\ndescription:\n" + func.desc
            output += "\n------\n"

        output += "KEYWORDS:\n"
        for key, keyword in readoc.keywords.items():
            output += keyword.name + ":" + keyword.desc + " / languages:" + ','.join(keyword.languages) + "\n"
        return output
