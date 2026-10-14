# Whisper Doped Distribution Plan

Goal: let a user download Whisper Doped from GitHub, end up with a real
`WhisperDoped.app` icon in `/Applications`, and use it exactly like the source
build — a menu-bar agent (rumps) with global hotkeys and Accessibility text
insertion, no full GUI.

## Chosen approach

**Primary — GitHub Releases: a `.dmg` containing `WhisperDoped.app`.**
Drag to Applications, launch once. This gives the app a stable bundle identity
so macOS attaches the Microphone / Accessibility / Input-Monitoring permissions
to *WhisperDoped* rather than to a Python interpreter.

**Secondary — `uvx` one-liner** for people who prefer the terminal and want
auto-updates:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
uvx "whisper-doped[macos,mlx] @ git+https://github.com/TotallyIndecisive/whisper-doped-v1" whisper-doped run
```

## How the bundle is built

`setup.py` (py2app) + `build_app.sh`:

1. Create/repair `.venv`, `pip install -e ".[macos,mlx]"`.
2. Run `py2app` (from the venv interpreter so MLX and PortAudio are present).
3. Copy the full **MLX** runtime into the bundle (see gotchas below).
4. Ad-hoc code-sign the bundle.
5. `create_dmg.sh` packages it with an Applications shortcut, a README and an
   `Install & Open.command` helper.

References to `LSUIElement: True` in the Info.plist keep it a menu-bar agent
(no Dock icon), which matches the current behaviour.

### Non-obvious gotchas that are handled

* **pyproject metadata vs py2app** — py2app 0.28 aborts with
  *"install_requires is no longer supported"* when setuptools reads
  `dependencies` from `pyproject.toml`. `build_app.sh` hides `pyproject.toml`
  for the duration of the build.
* **`pkg_resources` / `imp`** — py2app needs the legacy `pkg_resources`
  (dropped in setuptools ≥ 81) and the `imp` shim via `modulegraph` on
  Python 3.12+. The script pins `setuptools<81` and installs `modulegraph`.
* **`mlx` is a PEP 420 namespace package** — py2app cannot treat it as a
  `packages` entry. It copies only `mlx/core.so` and misses
  `mlx/lib/libmlx.dylib` and `mlx/lib/mlx.metallib`, so `import mlx.core`
  fails at `dlopen`. The script copies the whole installed `mlx/` tree next to
  `core.so`.
* **zip shadowing** — py2app also byte-compiles a *stub* `mlx/` package into
  `lib/python312.zip`, which shadows the real tree. The script strips `mlx/*`
  entries from the zip.
* **Pillow's stale signatures** — Pillow (unused) drags in `libtiff`/`liblzma`
  whose already-invalid ad-hoc signatures make `codesign --deep` fail. It is
  excluded, which lets the bundle sign cleanly.
* **Native runtime deps of `mlx_whisper`** — `mlx_whisper.timing` imports
  `scipy` and `numba` (which needs `llvmlite`), and the tokeniser needs
  `tiktoken`. All are bundled.
* **numpy star-import** — scipy's array-api shim does `from numpy import *`,
  which lazily triggers `numpy.testing` → `unittest`; `unittest` must not be
  excluded.

## Size

The bundle (`dist/WhisperDoped.app`) is ~620 MB; the compressed DMG is
~270 MB. Speech **models are not bundled** — they download from Hugging Face on
first use (~1.6 GB for the default `mlx-community/whisper-large-v3-turbo`,
much less for `whisper-tiny`).

## Code signing / Gatekeeper

The app is **ad-hoc** signed (`codesign --sign -`). That keeps the bundle
internally valid, but a *downloaded* (quarantined) ad-hoc app is still blocked
by Gatekeeper the first time. Users clear it once with any of:

* dual-clicking **`Install & Open.command`** in the DMG, or
* right-click → **Open** on the app, or
* `xattr -dr com.apple.quarantine /Applications/WhisperDoped.app`.

For a completely warning-free download you would need an Apple Developer ID
and notarization (paid). Without that, the quarantine step above is required —
this is normal for open-source macOS apps.

## Architecture

Built for Apple Silicon (arm64) because MLX is Apple-Silicon only. Intel Macs
should use the `uvx`/`pipx` route with the `whispercpp` or `fasterwhisper`
backend instead.

## Releases

1. `git tag v0.2.0 && git push origin v0.2.0`
2. `./build_app.sh && ./create_dmg.sh`
3. Create the GitHub Release and attach
   `dist/WhisperDoped-0.2.0-macOS-arm64.dmg`.
