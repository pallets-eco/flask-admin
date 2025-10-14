# Working with Babel translations
```bash
uv sync --group docs
```
## As a developer who's changed some text in Flask-Admin

Run `./babel.sh --update`

## As a translator who wants to find missing translations
Run `awk '/^msgid / {msgid=substr($0, 8, length($0)-8)} /^msgstr ""$/ {print msgid}' file.po`

## As a translator who's updated some `.po`/`.mo` files

Run `./babel.sh`
