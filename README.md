# Workspace Setups

An [Omarchy](https://omarchy.org/) shell plugin that lets you define named
work environments and open everything you need with a single click from the
status bar. Each setup launches its apps on their assigned Hyprland
workspaces, silently, and then focuses the workspace you choose.

## Features

- Bar icon listing your configured setups with a busy spinner while launching
- Sequential, predictable launching: focus workspace → launch app → wait for
  its window to map → move to the next app
- A standalone manager window (PyQt6) to create, edit and delete setups —
  changes apply instantly, no shell restart needed
- Config lives in `~/.config/omarchy/workspace-setups.json` and is hot-reloaded

## Install

```bash
omarchy plugin add https://github.com/KarelDiaz/workspaces-setups.git --enable
```

## Dependencies

- `hyprctl`, `uwsm-app` (ship with Omarchy/Hyprland)
- `jq` — used by the launcher script
- `python3` + `PyQt6` — used by the manager window

## Configuration

Click the bar icon → *Gestionar espacios…* to open the manager, or edit
`~/.config/omarchy/workspace-setups.json` directly:

```json
{
  "setups": [
    {
      "name": "Web dev",
      "icon": "🌐",
      "switchTo": 1,
      "apps": [
        { "workspace": 1, "command": "code" },
        { "workspace": 2, "command": "firefox" },
        { "workspace": 9, "command": "spotify" }
      ]
    }
  ]
}
```

- `name` (required): label shown in the bar popup
- `icon`: Nerd Font glyph or emoji shown next to the name
- `switchTo`: workspace focused after all apps are launched
- `apps[]`: each entry has a `workspace` number and a shell `command`

See [workspace-setups.example.json](workspace-setups.example.json).

## License

MIT — see [LICENSE](LICENSE).
