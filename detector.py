import os
import shutil
import subprocess


def _has(cmd):
    return shutil.which(cmd) is not None


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
    if _has("fastfetch"):
        return True

    print("fastfetch is not installed.")
    try:
        pick = input("can i try to install fastfetch now? [y/N]: ")
    except EOFError:
        return False

    if not _yes(pick):
        return False

    plans = _install_plans()
    if not plans:
        print("no supported package manager found. install fastfetch manually.")
        return False

    for plan in plans:
        if _run_plan(plan) and _has("fastfetch"):
            return True

    print("couldn't install fastfetch automatically.")
    return _has("fastfetch")
