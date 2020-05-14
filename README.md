# ReaScriptDocParser

This project aims to parse the [Reascript](https://www.reaper.fm/sdk/reascript/reascript.php) [HTML documentation](https://www.reaper.fm/sdk/reascript/reascripthelp.html) to any other format.

An intermediate representation of the documentation (class `ReaDoc`) 
is built and used by a parser (child of class `ReaDocParser`).

`ReaDoc` currently extract:
- Functions with their name, description, language, parameters (type, names and possible values) and return values (type and names)
- Keywords detected in functions' descriptions (e.g. gfx variables, 'parmname' possible values) along with their own description and their language.

[BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/) ([see doc](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)) is used in this project, 
to install it with pip, use the command : `pip install beautifulsoup4`

Below is a list of available parser.

## Visual Studio Code parser

This parser produce snippets for Visual Studio Code for all available languages (C, EEL, Lua and Python).

This parser provide 'with return' snippets with the following prefix : 
`reaperwr.FUNCTION_NAME` on lua and `WR_FUNCTION_NAME` on C, EEL and Python.

Example of 'with return' snippet in lua : 

`reaperwr.GetSetMediaTrackInfo_String` gives 
`local boolean retval, string stringNeedBig = reaper.GetSetMediaTrackInfo_String(MediaTrack tr, string parmname, string stringNeedBig, boolean setNewValue)`

Snippets can be found here: `snippets/reascript.code-snippets`

### Installation

#### Global User Snippet

Snippets will be available anywhere.

Copy the snippet to the following directory:
- Windows: `%APPDATA%\Code\User\snippets`
- macOS: `$HOME/Library/Application Support/Code/User/snippets`
- Linux: `$HOME/.config/Code/User/snippets`

#### Workspace Snippet

Snippets will be available only in the Reaper script folder.

Create a workspace in reaper script folder.

- Windows: `%APPDATA%\REAPER\Reascript`

Create a `.vscode` folder in reaper script folder and copy the snippet in it.

#### Misc.

If the theme that you use don't highlight operator (`or`, `and`, `not`), you can change
their color by adding the following code in your `settings.json` file (in folder `Code/User`)
or in your workspace settings:

```	
"editor.tokenColorCustomizations": {
"textMateRules": [
    {
        "scope": "keyword.operator.lua",
        "settings": {
            "foreground": "#569BD2"
        }
    }
]
}
```

If you find the suggestion window not wide enough, you can install [Custom CSS and JS Loader](https://marketplace.visualstudio.com/items?itemName=be5invis.vscode-custom-css)
and put in your `custom.css` the following code:

```
.monaco-editor .suggest-widget.docs-side {
  width: 1000px;
}

.monaco-editor .suggest-widget.docs-side > .details {
  width: 60%;
  max-height: 800px !important;
}

.monaco-editor .suggest-widget.docs-side > .tree {
  width: 30%;
  float: left;
}

.monaco-editor .suggest-widget {
  width: 600px;
}
```

## Raw parser

This is a readable / example parser.

Output: `snippets/reascript.txt`

## Making a custom parser

You can make your own parser by creating a `ReaDocParser` child class and 
by implementing its `parse` method.
