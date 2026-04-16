"""Build release artifacts for Windows and Linux desktop delivery."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
DIST = ROOT / "dist"
BUILD = ROOT / "build"
ARTIFACTS = ROOT / "artifacts"
ASSETS = ROOT / "packaging" / "assets"
WINDOWS_ISS = ROOT / "packaging" / "windows" / "FlowerVendingSimulator.iss"
APP_NAME = "FlowerVendingSimulator"
APP_SLUG = "flower-vending-simulator"
VERSION = "0.1.3"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "targets",
        nargs="+",
        choices=("windows-portable", "windows-installer", "linux-appimage"),
    )
    parser.add_argument(
        "--appimagetool",
        default=os.getenv("APPIMAGETOOL", ""),
        help="Path to appimagetool for Linux builds.",
    )
    args = parser.parse_args(argv)

    ARTIFACTS.mkdir(parents=True, exist_ok=True)

    for target in args.targets:
        if target == "windows-portable":
            build_windows_portable()
        elif target == "windows-installer":
            build_windows_installer()
        elif target == "linux-appimage":
            build_linux_appimage(appimagetool=Path(args.appimagetool) if args.appimagetool else None)
    return 0


def build_windows_portable() -> Path:
    exe = _run_pyinstaller(onefile=True)
    artifact = ARTIFACTS / f"{APP_NAME}-Windows-x64.exe"
    shutil.copy2(exe, artifact)
    return artifact


def build_windows_installer() -> Path:
    portable = build_windows_portable()
    iscc = _find_iscc()
    output_dir = ARTIFACTS.resolve()
    _run(
        [
            str(iscc),
            f"/DAppVersion={VERSION}",
            f"/DSourceExe={portable.resolve()}",
            f"/DSourceDocs={ROOT.resolve() / 'docs'}",
            f"/DOutputDir={output_dir}",
            str(WINDOWS_ISS),
        ]
    )
    return ARTIFACTS / f"{APP_NAME}-Setup-Windows-x64.exe"


def build_linux_appimage(*, appimagetool: Path | None) -> Path:
    if appimagetool is None:
        raise FileNotFoundError("appimagetool path is required for linux-appimage builds")
    bundle = _run_pyinstaller(onefile=False)
    if not bundle.is_dir():
        raise RuntimeError("expected onedir bundle for Linux packaging")

    appdir = BUILD / f"{APP_NAME}.AppDir"
    if appdir.exists():
        shutil.rmtree(appdir)
    (appdir / "usr" / "lib" / APP_SLUG).mkdir(parents=True, exist_ok=True)
    shutil.copytree(bundle, appdir / "usr" / "lib" / APP_SLUG, dirs_exist_ok=True)

    app_run = appdir / "AppRun"
    app_run.write_text(
        "#!/usr/bin/env bash\n"
        "HERE=\"$(cd \"$(dirname \"$0\")\" && pwd)\"\n"
        "exec \"$HERE/usr/lib/flower-vending-simulator/FlowerVendingSimulator\" \"$@\"\n",
        encoding="utf-8",
    )
    app_run.chmod(0o755)

    shutil.copy2(ASSETS / f"{APP_SLUG}.desktop", appdir / f"{APP_SLUG}.desktop")
    shutil.copy2(ASSETS / f"{APP_SLUG}.svg", appdir / f"{APP_SLUG}.svg")

    tarball = ARTIFACTS / f"{APP_NAME}-Linux-x86_64.tar.gz"
    with tarfile.open(tarball, "w:gz") as archive:
        archive.add(bundle, arcname=APP_NAME)

    artifact = ARTIFACTS / f"{APP_NAME}-Linux-x86_64.AppImage"
    env = os.environ.copy()
    env.setdefault("ARCH", "x86_64")
    _run([str(appimagetool.resolve()), str(appdir), str(artifact)], env=env)
    return artifact


def _run_pyinstaller(*, onefile: bool) -> Path:
    _require_pyinstaller()
    if DIST.exists():
        shutil.rmtree(DIST)
    pyinstaller_command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--name",
        APP_NAME,
        "--paths",
        str(SRC),
        "--add-data",
        _data_arg(ROOT / "config", "config"),
        "--add-data",
        _data_arg(ROOT / "docs", "docs"),
        "--add-data",
        _data_arg(SRC / "flower_vending" / "ui" / "assets", "flower_vending/ui/assets"),
        "--windowed",
        str(SRC / "flower_vending" / "runtime" / "product_launcher.py"),
    ]
    pyinstaller_command.append("--onefile" if onefile else "--onedir")
    _run(pyinstaller_command)
    if onefile:
        return DIST / f"{APP_NAME}.exe" if os.name == "nt" else DIST / APP_NAME
    return DIST / APP_NAME


def _data_arg(source: Path, destination: str) -> str:
    separator = ";" if os.name == "nt" else ":"
    return f"{source}{separator}{destination}"


def _find_iscc() -> Path:
    candidates = [
        shutil.which("ISCC.exe"),
        shutil.which("iscc"),
        Path(os.getenv("LOCALAPPDATA", "")) / "Programs" / "Inno Setup 6" / "ISCC.exe",
        Path(os.environ.get("ProgramFiles(x86)", "")) / "Inno Setup 6" / "ISCC.exe",
        Path(os.environ.get("ProgramFiles", "")) / "Inno Setup 6" / "ISCC.exe",
    ]
    for candidate in candidates:
        if not candidate:
            continue
        path = Path(candidate)
        if path.exists():
            return path
    raise FileNotFoundError("Inno Setup compiler (ISCC.exe) was not found")


def _require_pyinstaller() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "pip", "show", "pyinstaller"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError("PyInstaller is not installed. Run: python -m pip install pyinstaller")


def _run(command: list[str], *, env: dict[str, str] | None = None) -> None:
    subprocess.run(command, cwd=ROOT, check=True, env=env)


if __name__ == "__main__":
    raise SystemExit(main())
