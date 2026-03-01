import os
import shutil
import subprocess
import sys


def _has(cmd):
    return shutil.which(cmd) is not None


def _is_exec(path):
    return bool(path) and os.path.isfile(path) and os.access(path, os.X_OK)


def _first_exec(paths):
    for p in paths:
        if _is_exec(p):
            return p
    return None


def _brew_bin():
    b = shutil.which("brew")
    if b:
        return b
    return _first_exec([
        "/opt/homebrew/bin/brew",
        "/usr/local/bin/brew",
    ])


def find_fastfetch():
    hit = shutil.which("fastfetch")
    if hit:
        return hit

    if os.name == "nt":
        try:
            p = subprocess.run(["where", "fastfetch"], capture_output=True, text=True)
            if p.returncode == 0:
                for line in p.stdout.splitlines():
                    x = line.strip()
                    if x and os.path.exists(x):
                        return x
        except Exception:
            return None
        return None

    return _first_exec([
        "/opt/homebrew/bin/fastfetch",
        "/usr/local/bin/fastfetch",
        "/opt/local/bin/fastfetch",
        "/usr/bin/fastfetch",
    ])


def _yes(x):
    return x.strip().lower() in {"y", "yes"}


def _with_sudo(cmd):
    if os.name == "nt":
        return cmd
    try:
        root = os.geteuid() == 0
    except Exception:
        root = False
    if root or not _has("sudo"):
        return cmd
    return ["sudo"] + cmd


def _install_plans():
    plans = []

    if os.name == "nt":
        if _has("winget"):
            plans.append([["winget", "install", "--id", "Fastfetch-cli.Fastfetch", "-e", "--accept-package-agreements", "--accept-source-agreements"]])
        if _has("choco"):
            plans.append([["choco", "install", "fastfetch", "-y"]])
        if _has("scoop"):
            plans.append([["scoop", "install", "fastfetch"]])
        return plans

    if sys.platform == "darwin":
        brew = _brew_bin()
        if brew:
            plans.append([[brew, "install", "fastfetch"]])
        if _has("port"):
            plans.append([_with_sudo(["port", "install", "fastfetch"])])
        return plans

    if _has("pacman"):
        plans.append([_with_sudo(["pacman", "-Sy", "--noconfirm", "fastfetch"])])
    if _has("apt-get"):
        plans.append([_with_sudo(["apt-get", "update"]), _with_sudo(["apt-get", "install", "-y", "fastfetch"])])
    if _has("apt"):
        plans.append([_with_sudo(["apt", "update"]), _with_sudo(["apt", "install", "-y", "fastfetch"])])
    if _has("dnf"):
        plans.append([_with_sudo(["dnf", "install", "-y", "fastfetch"])])
    if _has("yum"):
        plans.append([_with_sudo(["yum", "install", "-y", "fastfetch"])])
    if _has("zypper"):
        plans.append([_with_sudo(["zypper", "--non-interactive", "install", "fastfetch"])])
    if _has("xbps-install"):
        plans.append([_with_sudo(["xbps-install", "-Sy", "fastfetch"])])
    if _has("apk"):
        plans.append([_with_sudo(["apk", "add", "fastfetch"])])

    brew = _brew_bin()
    if brew:
        plans.append([[brew, "install", "fastfetch"]])

    return plans


def _run_plan(plan):
    for cmd in plan:
        try:
            print("running:", " ".join(cmd))
            p = subprocess.run(cmd)
        except Exception:
            return False
        if p.returncode != 0:
            return False
    return True


def ensure_fastfetch():
    found = find_fastfetch()
    if found:
        return found

    print("fastfetch is not installed.")
    try:
        pick = input("can i try to install fastfetch now? [y/N]: ")
    except EOFError:
        return None

    if not _yes(pick):
        return None

    plans = _install_plans()
    if not plans:
        if sys.platform == "darwin":
            print("homebrew/macports not found. install Homebrew first, then run: brew install fastfetch")
        else:
            print("no supported package manager found. install fastfetch manually.")
        return None

    for plan in plans:
        if _run_plan(plan):
            got = find_fastfetch()
            if got:
                return got

    print("couldn't install fastfetch automatically.")
    if sys.platform == "darwin":
        print("try this manually: brew install fastfetch")
    return find_fastfetch()
