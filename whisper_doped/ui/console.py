"""Terminal UI: run dictation with only a global hotkey and stdout."""

from __future__ import annotations

import time


def run_console(config, dictapp, hotkeys) -> int:
    hotkeys.start()
    print(f"Whisper Doped - console mode  (backend: {type(dictapp.transcriber).__name__})")
    print(f"  mode         : {config.mode}")
    print(f"  push-to-talk : hold {config.push_to_talk_key}")
    print(f"  toggle combo : {config.toggle_combo}")
    print("  Ctrl+C to quit\n")
    dictapp.warmup()
    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nStopping\u2026")
    finally:
        dictapp.shutdown()
        hotkeys.stop()
    return 0
