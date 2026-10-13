"""Command-line entry point.

Subcommands:
    run         start dictation (menu bar on macOS by default, ``--console``
                for a terminal-only mode that also runs on Linux)
    transcribe  transcribe a WAV/MP3/… file and print the text
    insert      insert text into the focused app after a short countdown
    history     list recent dictations
    dict        manage the personal dictionary
    devices     list audio input devices
    backends    show which speech-recognition backends are usable here
    selftest    check the environment without needing a microphone
"""

from __future__ import annotations

import argparse
import sys
import time

from . import __version__


# ---------------------------------------------------------------------- helpers
def _set_model_for(config, model: str) -> None:
    """Set the model field belonging to the active ASR backend."""
    from .asr.factory import resolve_backend

    try:
        name = resolve_backend(config.asr_backend)
    except Exception:
        name = None
    if name == "mlx":
        config.model = model
    elif name == "whispercpp":
        config.whispercpp_model = model
    elif name == "fasterwhisper":
        config.fasterwhisper_model = model
    else:
        config.model = model


def _print_hotkeys(config) -> None:
    print(f"Whisper Doped {__version__}")
    print(f"  mode         : {config.mode}")
    print(f"  push-to-talk : hold {config.push_to_talk_key}")
    print(f"  toggle combo : {config.toggle_combo}")


# --------------------------------------------------------------------------- run
def cmd_run(args: argparse.Namespace) -> int:
    from .app import DictationApp
    from .asr import create_transcriber
    from .config import Config, DB_PATH
    from .hotkey import HotkeyManager
    from .storage import Store
    from .system import accessibility_trusted, request_accessibility_prompt
    from .ui import create_overlay, run as run_ui

    config = Config.load()
    if args.mode:
        config.mode = args.mode
    if args.backend:
        config.asr_backend = args.backend
    if args.model:
        _set_model_for(config, args.model)
    if args.no_polish:
        config.polish = False
    if args.console:
        config.ui = "console"  # offline-friendly: no menu bar / overlay
    config.save()

    store = Store(DB_PATH)
    transcriber = create_transcriber(config)
    overlay = create_overlay(config)
    dictapp = DictationApp(config, store, transcriber=transcriber, overlay=overlay, log=print)

    # First-run permission: ask macOS to add us to the Accessibility list so the
    # global hotkey and the synthetic paste work. Harmless when already granted.
    if not accessibility_trusted():
        print("Requesting Accessibility permission (needed for the hotkey and auto-typing)\u2026")
        request_accessibility_prompt()

    hotkeys = HotkeyManager(
        mode=config.mode,
        push_to_talk_key=config.push_to_talk_key,
        toggle_combo=config.toggle_combo,
        on_start=dictapp.begin,
        on_stop=dictapp.end,
    )

    print(f"ASR backend : {transcriber.describe()}")
    print(f"Insertion   : {dictapp.inserter.name}")
    _print_hotkeys(config)
    print()

    return run_ui(config, dictapp, hotkeys, store)


# -------------------------------------------------------------------- transcribe
def cmd_transcribe(args: argparse.Namespace) -> int:
    from .asr import create_transcriber
    from .config import Config, DB_PATH
    from .polish import Polisher
    from .storage import Store

    config = Config.load()
    if args.backend:
        config.asr_backend = args.backend
    if args.model:
        _set_model_for(config, args.model)
    if args.language:
        config.language = args.language

    store = Store(DB_PATH)
    transcriber = create_transcriber(config)
    result = transcriber.transcribe_file(args.path, initial_prompt=store.initial_prompt() or None)
    print(f"[{result.backend}/{result.language}] ({result.latency_ms} ms)")
    print(result.text)
    if args.polish:
        print("\n-- polished --")
        print(Polisher(store=store, enabled=True).polish(result.text))
    return 0


# ------------------------------------------------------------------------ insert
def cmd_insert(args: argparse.Namespace) -> int:
    from .config import Config
    from .insert import create_inserter

    config = Config.load()
    inserter = create_inserter(config)
    if not inserter.available():
        print(f"Warning: {inserter.name} inserter is not usable here "
              f"(need APIs/tools for this platform).", file=sys.stderr)
    text = args.text if args.text is not None else sys.stdin.read()
    for remaining in range(args.delay, 0, -1):
        print(f"inserting in {remaining}\u2026", end="\r", flush=True)
        time.sleep(1)
    method = inserter.insert(text)
    print(f"\ninserted via {method}")
    return 0


# ----------------------------------------------------------------------- history
def cmd_history(args: argparse.Namespace) -> int:
    from .config import DB_PATH
    from .storage import Store

    store = Store(DB_PATH)
    rows = store.recent(args.limit)
    if not rows:
        print("No dictations yet.")
        return 0
    for r in rows:
        ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(r.created_ts))
        app = r.app_name or "?"
        print(f"{ts}  [{app}]  ({r.duration_ms} ms rec, {r.latency_ms} ms asr, {r.insert_method})")
        print(f"    {r.final_text}")
    return 0


# -------------------------------------------------------------------- dictionary
def cmd_dict(args: argparse.Namespace) -> int:
    from .config import DB_PATH
    from .storage import Store, format_terms

    store = Store(DB_PATH)
    if args.action == "list":
        print(format_terms(store.terms()))
    elif args.action == "add":
        store.add_term(args.phrase, args.replacement or "", args.kind)
        print(f"added ({args.kind}): {args.phrase}")
    elif args.action == "remove":
        store.remove_term(args.phrase)
        print(f"removed: {args.phrase}")
    return 0


# ----------------------------------------------------------------------- devices
def cmd_devices(_args: argparse.Namespace) -> int:
    from .audio import list_devices

    print(list_devices())
    return 0


# ---------------------------------------------------------------------- backends
def cmd_backends(_args: argparse.Namespace) -> int:
    from .asr import available_backends
    from .config import Config
    from .insert import create_inserter

    print("Speech-recognition backends:")
    for name, ok in available_backends().items():
        flag = "available" if ok else "missing dep"
        print(f"  {name:14s} {flag}")

    config = Config.load()
    try:
        inserter = create_inserter(config)
        print(f"Insertion backend : {inserter.name} (usable: {inserter.available()})")
    except Exception as exc:
        print(f"Insertion backend : <error: {exc}>")
    return 0


# ---------------------------------------------------------------------- selftest
def cmd_selftest(_args: argparse.Namespace) -> int:
    import tempfile
    from pathlib import Path

    ok = True
    print(f"Whisper Doped {__version__} self-test\n")

    from .platform_info import arch, is_apple_silicon, is_linux, is_macos, module_available

    print(f"Platform: {sys.platform} ({arch()})  "
          f"macOS={is_macos()} Linux={is_linux()} AppleSilicon={is_apple_silicon()}")
    print("Python:", sys.version.split()[0])
    for mod in ["numpy", "sounddevice", "pynput"]:
        try:
            __import__(mod)
            print(f"  [ok]   {mod}")
        except Exception as exc:
            ok = False
            print(f"  [FAIL] {mod}: {exc}")

    print("\nASR backends:")
    from .asr import available_backends

    for name, avail in available_backends().items():
        dep = {"mlx": "mlx-whisper", "whispercpp": "pywhispercpp", "fasterwhisper": "faster-whisper"}[name]
        status = "ok" if avail else f"missing ({dep})"
        print(f"  [{('ok' if avail else '--')}] {name:13s} {status}")
        if name == "mlx" and not avail and not is_apple_silicon():
            print("           (MLX needs Apple Silicon)")

    print("\nPermissions:" if is_macos() else "\nPermissions (macOS only):")
    from .system import accessibility_trusted

    if is_macos():
        print("  Accessibility:", "granted" if accessibility_trusted() else "NOT granted (needed for insertion + hotkeys)")
    else:
        print("  n/a (not macOS)")

    print("\nInsertion:")
    from .config import Config
    from .insert import create_inserter

    inserter = create_inserter(Config.load())
    print(f"  backend: {inserter.name}  usable: {inserter.available()}")

    print("\nPolish rules:")
    from .polish import Polisher

    p = Polisher()
    samples = [
        ("um so the the meeting is at 5 actually 6pm", "So the meeting is at 6pm."),
        ("hello comma world period", "Hello, world."),
        ("i think i think we should ship it", "I think we should ship it."),
    ]
    for raw, expected in samples:
        got = p.polish(raw)
        flag = "ok" if got == expected else "check"
        print(f"  [{flag}] {raw!r} -> {got!r}")

    print("\nDatabase:")
    try:
        from .storage import Store

        with tempfile.TemporaryDirectory() as td:
            s = Store(Path(td) / "t.sqlite")
            s.add_history("raw", "final", app_name="Test")
            s.add_term("Whisper Doped", "", "vocabulary")
            print(f"  [ok]   history rows: {s.history_count()}, terms: {len(s.terms())}")
        from .config import data_dir

        print(f"  data dir: {data_dir()}")
    except Exception as exc:
        ok = False
        print(f"  [FAIL] {exc}")

    if not ok:
        sys.exit(1)


# --------------------------------------------------------------------------- main
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="whisper-doped",
        description="Local, private dictation for macOS and Linux.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command")

    run = sub.add_parser("run", help="start dictation")
    run.add_argument("--console", action="store_true", help="terminal only (no menu bar / overlay)")
    run.add_argument("--mode", choices=["push_to_talk", "toggle"], default=None)
    run.add_argument("--backend", choices=["auto", "mlx", "whispercpp", "fasterwhisper"],
                     default=None, help="speech-recognition backend")
    run.add_argument("--model", default=None, help="model for the active backend")
    run.add_argument("--no-polish", action="store_true")
    run.set_defaults(func=cmd_run)

    tr = sub.add_parser("transcribe", help="transcribe an audio file")
    tr.add_argument("path")
    tr.add_argument("--backend", choices=["auto", "mlx", "whispercpp", "fasterwhisper"], default=None)
    tr.add_argument("--model", default=None)
    tr.add_argument("--language", default=None)
    tr.add_argument("--polish", action="store_true")
    tr.set_defaults(func=cmd_transcribe)

    ins = sub.add_parser("insert", help="insert text into the focused app")
    ins.add_argument("text", nargs="?", default=None)
    ins.add_argument("--delay", type=int, default=3, help="countdown seconds")
    ins.set_defaults(func=cmd_insert)

    hist = sub.add_parser("history", help="list recent dictations")
    hist.add_argument("-n", "--limit", type=int, default=20)
    hist.set_defaults(func=cmd_history)

    d = sub.add_parser("dict", help="manage the personal dictionary")
    d.add_argument("action", choices=["list", "add", "remove"])
    d.add_argument("phrase", nargs="?", default="")
    d.add_argument("--replacement", default="")
    d.add_argument("--kind", choices=["vocabulary", "replacement", "snippet"], default="vocabulary")
    d.set_defaults(func=cmd_dict)

    sub.add_parser("devices", help="list audio input devices").set_defaults(func=cmd_devices)
    sub.add_parser("backends", help="list usable speech-recognition backends").set_defaults(func=cmd_backends)
    sub.add_parser("selftest", help="check the environment").set_defaults(func=cmd_selftest)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "command", None):
        args = parser.parse_args(["run"])
    return int(args.func(args) or 0)


if __name__ == "__main__":
    raise SystemExit(main())