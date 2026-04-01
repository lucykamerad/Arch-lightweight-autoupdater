# Arch-lightweight-autoupdater

A lightweight, modern system updater for **Arch Linux**.

## Features
- **Modern UI**: Clean, dark-themed interface built with standard Tkinter (no bloat).
- **Security-First**: No more stored passwords. Uses `pkexec` (PolicyKit) for secure, standard privilege escalation.
- **AUR Support**: Automatically detects and uses `yay` or `paru` if available.
- **Arch Verification**: Safety check to ensure it only runs on Arch Linux systems.
- **Lightweight**: Zero external dependencies beyond standard Python libraries and Polkit.

## Usage
1. Ensure `polkit` is installed (it usually is on most DEs).
2. Launch the app manually or add it to your startup applications.
3. Click "Check & Update" to begin.

## Security
This app uses `pkexec` to run `pacman` with root privileges. This means you will be prompted by your system's standard authentication agent (e.g., GNOME Polkit, KDE Polkit), ensuring your password is never stored or handled by this script.

## License
Provided under the [MIT License](LICENSE).

---
- **Author**: Lucia Ushka <3
