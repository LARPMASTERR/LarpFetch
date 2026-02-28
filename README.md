# LARP-Fetch

LARP-Fetch is a neofetch-adjacent Python CLI that shows real system info from `fastfetch` while letting you pick a custom Fastfetch ASCII logo.

## Requirements

- Python 3
- `fastfetch` in `PATH` (or let LARP-Fetch try to install it)

## Usage

```bash
python larpfetch.py arch
```

You can use:

- `arch`
- `ubuntu`
- `mint`
- `fedora`
- `gentoo`
- `popos`
- `steamos`
- `windows`
- `macos`

If `fastfetch` is missing, LARP-Fetch asks if it should try installing it.

The output always ends with:

`using LARP-Fetch`
