<div align="center">

# UKey Core Firmware

Open-source firmware for UKey Core hardware wallets.

[![GitHub Stars](https://img.shields.io/github/stars/bestyourwallet/firmware-core?style=for-the-badge\&logo=github\&labelColor=000)](https://github.com/bestyourwallet/firmware-core/stargazers)
[![Release](https://img.shields.io/github/v/release/bestyourwallet/firmware-core?style=for-the-badge\&labelColor=000)](https://github.com/bestyourwallet/firmware-core/releases)
[![Contributors](https://img.shields.io/github/contributors-anon/bestyourwallet/firmware-core?style=for-the-badge\&labelColor=000)](https://github.com/bestyourwallet/firmware-core/graphs/contributors)
[![Last Commit](https://img.shields.io/github/last-commit/bestyourwallet/firmware-core?style=for-the-badge\&labelColor=000)](https://github.com/bestyourwallet/firmware-core/commits)

</div>

## Getting Started

### 1. Install Nix

Install [Nix](https://nixos.org/download.html).

### 2. Clone the repository

```bash
git clone --recurse-submodules https://github.com/bestyourwallet/firmware-core.git
cd firmware-core
```

### 3. Setup the development environment

```bash
nix-shell
poetry install
```

### 4. Build the emulator

```bash
cd core
poetry run make build_unix
```

### 5. Run the emulator

```bash
poetry run ./emu.py
```

## Python Client

Install the Python client for communicating with UKey devices or the emulator:

```bash
cd python
poetry run python3 -m pip install .
```

## Contributing

Contributions are welcome.

Bug fixes, improvements, and new features can be submitted through Pull Requests.

## Security

If you discover a security vulnerability, please do not disclose it in a public GitHub issue.

## License

See the repository license for details.
