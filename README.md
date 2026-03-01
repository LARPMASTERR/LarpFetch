# LARP-Fetch

LARP-Fetch is a neofetch-adjacent Python CLI that shows real system info from `fastfetch` while letting you pick a custom Fastfetch ASCII logo.

## Requirements

- Python 3
- `fastfetch` (if missing, LARP-Fetch can try to install it)

### Platform install support

- Linux: `pacman`, `apt/apt-get`, `dnf`, `yum`, `zypper`, `xbps-install`, `apk`
- Windows: `winget`, `choco`, `scoop`
- macOS: `brew` (Homebrew), `port` (MacPorts)

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
- `cachyos`

If `fastfetch` is missing, LARP-Fetch asks if it should try installing it.

The output always ends with:

`using LARP-Fetch`
