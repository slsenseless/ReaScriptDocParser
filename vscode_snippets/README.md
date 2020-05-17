# Visual Studio Code snippets

## Code snippets descriptions

- `reascript.code-snippets` gives REAPER snippets and keywords from the official documentation. 
- `reascript_usdoc.code-snippets` gives REAPER snippets and keywords from the Ultraschall documentation.
It is recommended over `reascript.code-snippets` since it provides additionnal descriptions.
- `ultraschall.code-snippets` gives snippets for Ultraschall API.
- `reaper_action_list.code-snippets` gives REAPER command ID description and snippets to get ID
(E.g. writing `MAIN_TRACK_TOGGLE_MUTE_FOR_SELECTED_TRACKS` will give its corresponding ID `6`).
It is usefull if you use `reaper.OnCommand` a lot in your scripts.
- `sws_action_list.code-snippets` gives SWS command ID description and snippets to get ID.
It is usefull if you use `reaper.NamedCommandLookup` a lot in your scripts.
- `reascript_vp.code-snippets` gives snippets for video-processor for EEL language. (You probably don't need it)

## Installation

### Global User Snippet

Snippets will be available anywhere.

Copy the snippet to the following directory:
- Windows: `%APPDATA%\Code\User\snippets`
- macOS: `$HOME/Library/Application Support/Code/User/snippets`
- Linux: `$HOME/.config/Code/User/snippets`

### Workspace Snippet

Snippets will be available only in the Reaper script folder.

Create a workspace in reaper script folder.

- Windows: `%APPDATA%\REAPER\Reascript`

Create a `.vscode` folder in reaper script folder and copy the snippet in it.

### Misc.

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
