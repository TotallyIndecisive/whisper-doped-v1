"""macOS floating "pill" that shows dictation state.

The original renders a floating Electron panel near the bottom of the screen
("FloatingWebPanel"). We build the same idea as a native, click-through
``NSPanel`` with a translucent HUD material.

All AppKit work must happen on the main thread. ``setup`` is called once from
the run loop's thread before the app starts; ``show``/``hide`` are safe to call
from any thread and marshal themselves onto the main thread.
"""

from __future__ import annotations


class MacOverlay:
    def __init__(self, width: int = 280, height: int = 56, bottom_offset: int = 120) -> None:
        self.width = width
        self.height = height
        self.bottom_offset = bottom_offset
        self._panel = None
        self._label = None
        self._ok = False

    # ---------------------------------------------------------------- main thread
    def setup(self) -> bool:
        try:
            from AppKit import (  # type: ignore
                NSPanel,
                NSScreen,
                NSTextField,
                NSColor,
                NSFont,
                NSFloatingWindowLevel,
                NSBackingStoreBuffered,
                NSWindowStyleMaskBorderless,
                NSWindowCollectionBehaviorCanJoinAllSpaces,
                NSWindowCollectionBehaviorFullScreenAuxiliary,
                NSWindowCollectionBehaviorStationary,
                NSVisualEffectView,
                NSVisualEffectMaterialHUDWindow,
                NSVisualEffectBlendingModeBehindWindow,
                NSVisualEffectStateActive,
                NSViewWidthSizable,
                NSViewHeightSizable,
            )
            from Foundation import NSMakeRect  # type: ignore

            screen = NSScreen.mainScreen().frame()
            x = (screen.size.width - self.width) / 2.0
            y = float(self.bottom_offset)
            rect = NSMakeRect(x, y, self.width, self.height)

            panel = NSPanel.alloc().initWithContentRect_styleMask_backing_defer_(
                rect, NSWindowStyleMaskBorderless, NSBackingStoreBuffered, False
            )
            panel.setLevel_(NSFloatingWindowLevel)
            panel.setOpaque_(False)
            panel.setBackgroundColor_(NSColor.clearColor())
            panel.setHasShadow_(True)
            panel.setIgnoresMouseEvents_(True)
            panel.setCollectionBehavior_(
                NSWindowCollectionBehaviorCanJoinAllSpaces
                | NSWindowCollectionBehaviorStationary
                | NSWindowCollectionBehaviorFullScreenAuxiliary
            )

            content = panel.contentView()
            content.setWantsLayer_(True)
            try:
                content.layer().setCornerRadius_(self.height / 2.0)
                content.layer().setMasksToBounds_(True)
            except Exception:
                pass

            effect = NSVisualEffectView.alloc().initWithFrame_(NSMakeRect(0, 0, self.width, self.height))
            effect.setMaterial_(NSVisualEffectMaterialHUDWindow)
            effect.setBlendingMode_(NSVisualEffectBlendingModeBehindWindow)
            effect.setState_(NSVisualEffectStateActive)
            effect.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)
            content.addSubview_(effect)

            label = NSTextField.alloc().initWithFrame_(NSMakeRect(12, 0, self.width - 24, self.height))
            label.setStringValue_("")
            label.setBezeled_(False)
            label.setDrawsBackground_(False)
            label.setEditable_(False)
            label.setSelectable_(False)
            label.setAlignment_(1)
            label.setTextColor_(NSColor.whiteColor())
            try:
                label.setFont_(NSFont.systemFontOfSize_weight_(14.0, 0.25))
            except Exception:
                label.setFont_(NSFont.systemFontOfSize_(14.0))
            effect.addSubview_(label)

            self._panel = panel
            self._label = label
            self._ok = True
            return True
        except Exception:
            self._ok = False
            return False

    # -------------------------------------------------------------- any thread
    def show(self, text: str = "Listening\u2026") -> None:
        if not self._ok:
            return
        try:
            from PyObjCTools import AppHelper  # type: ignore

            AppHelper.callAfter(self._show_main, text)
        except Exception:
            pass

    def update(self, text: str) -> None:
        self.show(text)

    def hide(self) -> None:
        if not self._ok:
            return
        try:
            from PyObjCTools import AppHelper  # type: ignore

            AppHelper.callAfter(self._hide_main)
        except Exception:
            pass

    def _show_main(self, text: str) -> None:
        try:
            if self._label is not None:
                self._label.setStringValue_(text)
            if self._panel is not None:
                self._panel.orderFrontRegardless()
        except Exception:
            pass

    def _hide_main(self) -> None:
        try:
            if self._panel is not None:
                self._panel.orderOut_(None)
        except Exception:
            pass
