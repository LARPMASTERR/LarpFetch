import importlib
import json
import re
import subprocess
import sys
import time

from detector import ensure_fastfetch, find_fastfetch

logos = {
    "arch": "arch",
    "ubuntu": "ubuntu",
    "mint": "mint",
    "fedora": "fedora",
    "gentoo": "gentoo",
    "popos": "popos",
    "steamos": "steamos",
    "windows": "windows",
    "macos": "macos",
    "cachyos": "cachyos",
}

base_bits = {
    "$0": "\033[0m",
    "$1": "\033[31m",
    "$2": "\033[32m",
    "$3": "\033[33m",
    "$4": "\033[34m",
    "$5": "\033[35m",
    "$6": "\033[36m",
    "$7": "\033[37m",
    "$8": "\033[90m",
    "$9": "\033[97m",
}

logo_bits = {
    "arch": {"$1": "\033[97m", "$2": "\033[36m"},
    "ubuntu": {"$1": "\033[97m", "$2": "\033[38;5;208m"},
    "mint": {"$1": "\033[97m", "$2": "\033[38;5;42m"},
    "fedora": {"$1": "\033[97m", "$2": "\033[38;5;27m"},
    "gentoo": {"$1": "\033[97m", "$2": "\033[38;5;135m"},
    "popos": {"$1": "\033[97m", "$2": "\033[38;5;39m"},
    "steamos": {"$1": "\033[97m", "$2": "\033[38;5;39m"},
    "windows": {"$1": "\033[38;5;39m", "$2": "\033[38;5;75m", "$3": "\033[38;5;117m", "$4": "\033[38;5;81m"},
    "macos": {"$2": "\033[38;5;196m", "$3": "\033[38;5;208m", "$4": "\033[38;5;220m", "$5": "\033[38;5;82m", "$6": "\033[38;5;39m"},
    "cachyos": {"$1": "\033[97m", "$2": "\033[38;5;45m", "$3": "\033[38;5;39m"},
}


def pick_logo(modname):
    try:
        m = importlib.import_module(modname)
    except Exception:
        return ""
    for k, v in m.__dict__.items():
        if k.startswith("__"):
            continue
        if isinstance(v, str):
            return v.rstrip("\n")
    return ""


def paint(x, logo_key=None):
    out = x
    bits = dict(base_bits)
    if logo_key in logo_bits:
        bits.update(logo_bits[logo_key])
    for token, color in bits.items():
        out = out.replace(token, color)
    return out + "\033[0m"


def _fmt_secs(sec):
    try:
        s = int(sec)
    except Exception:
        return str(sec)
    days = s // 86400
    s = s % 86400
    hrs = s // 3600
    s = s % 3600
    mins = s // 60
    bits = []
    if days:
        bits.append(f"{days}d")
    if hrs:
        bits.append(f"{hrs}h")
    if mins or not bits:
        bits.append(f"{mins}m")
    return " ".join(bits)


def _fmt_mem(b):
    try:
        n = int(b)
    except Exception:
        return str(b)
    gib = n / (1024 * 1024 * 1024)
    if gib >= 100:
        return f"{gib:.0f} GiB"
    return f"{gib:.1f} GiB"


def _cmd(cmd):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True)
    except Exception:
        return ""
    if p.returncode != 0:
        return ""
    return p.stdout.strip()


def _grab_pref(text, keys):
    for line in text.splitlines():
        s = line.strip()
        for k in keys:
            needle = k + ":"
            if s.startswith(needle):
                return s.split(":", 1)[1].strip()
    return ""


def from_json(fastfetch_bin):
    p = subprocess.run([fastfetch_bin, "--json"], capture_output=True, text=True)
    if p.returncode != 0:
        return None
    try:
        rows = json.loads(p.stdout)
    except Exception:
        return None

    got = {}
    for r in rows:
        t = r.get("type")
        if not t:
            continue
        if "result" in r:
            got[t] = r.get("result")

    out = []

    osr = got.get("OS")
    if isinstance(osr, dict):
        osname = osr.get("prettyName") or osr.get("name") or ""
        if osname:
            out.append(("OS", osname))

    kr = got.get("Kernel")
    if isinstance(kr, dict):
        kv = (kr.get("name", "") + " " + kr.get("release", "")).strip()
        if kv:
            out.append(("Kernel", kv))

    up = got.get("Uptime")
    if isinstance(up, dict):
        u = up.get("uptime")
        if u is not None:
            out.append(("Uptime", _fmt_secs(u)))

    pk = got.get("Packages")
    if isinstance(pk, dict):
        total = pk.get("all")
        if total is not None:
            out.append(("Packages", str(total)))

    cpu = got.get("CPU")
    if isinstance(cpu, dict):
        c = cpu.get("cpu", "")
        cores = cpu.get("cores") if isinstance(cpu.get("cores"), dict) else {}
        logical = cores.get("logical")
        if c:
            if logical:
                out.append(("CPU", f"{c} ({logical} threads)"))
            else:
                out.append(("CPU", c))

    gpu = got.get("GPU")
    if isinstance(gpu, list) and gpu:
        names = []
        for g in gpu:
            if isinstance(g, dict):
                n = g.get("name")
                if n:
                    names.append(str(n))
        if names:
            out.append(("GPU", " | ".join(names)))

    mem = got.get("Memory")
    if isinstance(mem, dict):
        used = mem.get("used")
        total = mem.get("total")
        if used is not None and total is not None:
            out.append(("RAM", f"{_fmt_mem(used)} / {_fmt_mem(total)}"))
        elif total is not None:
            out.append(("RAM", _fmt_mem(total)))

    sh = got.get("Shell")
    if isinstance(sh, dict):
        sn = sh.get("prettyName") or sh.get("exeName")
        sv = sh.get("version")
        if sn and sv:
            out.append(("Shell", f"{sn} {sv}"))
        elif sn:
            out.append(("Shell", sn))

    de = got.get("DE")
    if isinstance(de, dict):
        dn = de.get("prettyName")
        dv = de.get("version")
        if dn and dv:
            out.append(("DE", f"{dn} {dv}"))
        elif dn:
            out.append(("DE", dn))

    wm = got.get("WM")
    if isinstance(wm, dict):
        wn = wm.get("prettyName")
        if wn:
            out.append(("WM", wn))

    return out if out else None


def from_plain(fastfetch_bin):
    p = subprocess.run([fastfetch_bin, "--logo", "none"], capture_output=True, text=True)
    if p.returncode != 0:
        return []

    ansi = re.compile(r"\x1b\[[0-9;]*m")
    out = []
    for row in p.stdout.splitlines():
        s = ansi.sub("", row).strip()
        if ":" not in s:
            continue
        k, v = s.split(":", 1)
        key = k.strip()
        val = v.strip()
        if not key or not val:
            continue
        low = key.lower()
        if low.startswith("os"):
            out.append(("OS", val))
        elif low.startswith("kernel"):
            out.append(("Kernel", val))
        elif low.startswith("uptime"):
            out.append(("Uptime", val))
        elif low.startswith("packages"):
            out.append(("Packages", val))
        elif low.startswith("cpu"):
            out.append(("CPU", val))
        elif low.startswith("gpu"):
            out.append(("GPU", val))
        elif low.startswith("memory") or low.startswith("ram"):
            out.append(("RAM", val))

    if out:
        return out
    cleaned = [ansi.sub("", x).rstrip() for x in p.stdout.splitlines() if x.strip()]
    return [("Info", x) for x in cleaned]


def show_info(fastfetch_bin):
    rows = from_json(fastfetch_bin)
    if not rows:
        rows = from_plain(fastfetch_bin)
    for k, v in rows:
        print(f"{k}: {v}")


def show_macos_specs():
    txt = pick_logo("macos")
    if txt:
        print(paint(txt, "macos"))

    fake = [
        ("OS", "macOS Tahoe 26.0"),
        ("Kernel", "Darwin 24.0.0"),
        ("CPU", "Apple M2"),
        ("GPU", "Apple M2"),
        ("RAM", "16 GB"),
        ("Uptime", "7d 4h 12m"),
        ("Packages", "214"),
        ("Shell", "zsh 5.9"),
        ("Model", "MacBook Air (13-inch, M2, 2022)"),
    ]

    for k, v in fake:
        print(f"{k}: {v}")

    print("using LARP-Fetch")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: python larpfetch.py arch")
        print("choices: " + ", ".join(logos.keys()))
        raise SystemExit(1)

    choice = sys.argv[1].strip().lower()

    if choice in {"macspecs", "mac-specs", "macos-specs"}:
        raise SystemExit(show_macos_specs())

    if choice not in logos:
        print("unknown ascii. pick one:", ", ".join(logos.keys()))
        raise SystemExit(1)

    ff = find_fastfetch()
    if not ff:
        ff = ensure_fastfetch()
    if not ff:
        print("install fastfetch and run again.")
        raise SystemExit(1)

    txt = pick_logo(logos[choice])
    if txt:
        print(paint(txt, choice))
    show_info(ff)
    print("using LARP-Fetch")
