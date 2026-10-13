# Whisper Doped Homebrew formula (CLI)

This Ruby formula lets users install the command-line version with:

    brew tap YOU/whisper-doped
    brew install whisper-doped

To make it work:

1. Publish this project to GitHub, then create a **separate tap repo** named
   `homebrew-whisper-doped` and copy this file to `Formula/whisper-doped.rb`.
   (Homebrew taps must be named `homebrew-<name>`.)
2. Publish the package to PyPI so `pip` can find the source tarball, then
   replace `url` and `sha256` below with the sdist values:
       pip download whisper-doped --no-binary :all: --no-deps -d .
       shasum -a 256 whisper_doped-0.2.0.tar.gz
3. Update `homepage` to your repository URL.

Notes
- A bare formula installs the CLI *core* (numpy/sounddevice/pynput), which is
  fully functional as a terminal dictation tool on macOS and Linux.
- For the full macOS experience (menu bar + Accessibility insertion), the
  simplest path for users is:  `pipx install "whisper-doped[macos,mlx]"`.
  Alternatively add the pyobjc wheels as extra `resource`s below.
- DMG/`.app` + `Casks/whisper-doped.rb` is the separate "dedicated app" track
  (requires a signed + notarized build), not this formula.
"""

class WhisperDoped < Formula
  include Language::Python::Virtualenv

  desc "Local, private dictation for macOS and Linux (Whisper-based)"
  homepage "https://github.com/YOUR_GITHUB_USERNAME/whisper-doped"
  url "https://files.pythonhosted.org/packages/source/w/whisper-doped/whisper_doped-0.2.0.tar.gz"
  sha256 "REPLACE_WITH_SDIST_SHA256"
  license "MIT"

  depends_on "python@3.12"

  # sounddevice ships the PortAudio library inside its wheels, so no extra
  # system audio dependency is required.

  def install
    virtualenv_install_with_resources
  end

  test do
    assert_match "whisper-doped", shell_output("#{bin}/whisper-doped --version")
  end
end