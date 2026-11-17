# Installation guide (how-to)

Goal: Wilson running at `http://localhost:8000` on your machine.

## Prerequisites

| Requirement | Needed for | Notes |
|---|---|---|
| Windows 10/11 x64 | Windows installer path | No Python needed; the installer bundles its own runtime |
| Python 3.12 or 3.13 | Linux/macOS from-source path | See [Python version notes](#python-version-notes) for 3.14 |
| C++ toolchain (Linux: `build-essential`; macOS: Xcode CLT; or `clang++`) | Only on Python versions without a prebuilt wheel for `fast-diff-match-patch` (an eyecite dependency) | Most users on 3.12/3.13 do not hit this |
| [CourtListener API token](https://www.courtlistener.com/sign-in/) | Phases 1-2 | Free |
| [Ollama](https://ollama.com) | Phase 3 coherence checking | Optional; Wilson falls back to CourtListener semantic search without it |

## Windows installer

1. Download `Wilson-Setup-0.1.1.exe` from [Releases](https://github.com/National-Standard-Consulting/wilson/releases).
2. Run it. No admin rights required; it installs into your user folder.
3. First launch runs a wizard: paste your CourtListener token, optionally download the bulk citation CSV (~1.9 GB compressed), optionally point at Ollama.
4. Start Wilson with `Wilson.bat`; your browser opens the interface automatically.

Everything lives in the Wilson folder. Uninstalling is deleting it.

## Linux / macOS from source

```bash
git clone https://github.com/National-Standard-Consulting/wilson.git
cd wilson
chmod +x setup.sh
./setup.sh
```

`setup.sh` is idempotent and safe to re-run. It creates `venv/`, installs dependencies, and creates `.env` from `.env.example`. Add your CourtListener token to `.env`, then:

```bash
source venv/bin/activate
uvicorn api:app --host 0.0.0.0 --port 8000
```

## Manual setup

```bash
git clone https://github.com/National-Standard-Consulting/wilson.git
cd wilson
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then edit .env and add your CourtListener token
uvicorn api:app --host 0.0.0.0 --port 8000
```

## Python version notes

`eyecite` depends on `fast-diff-match-patch`, a C++ extension. On Python versions without a prebuilt wheel (currently 3.14+), pip compiles it and the build invokes `clang++`. If installation fails on this package, either install `clang` or use Python 3.12/3.13. CI tests on 3.12 and 3.13.

## Optional: local bulk citation data

Phase 1 works without this (API lookup). The CSV makes existence checks fast and offline-capable:

```bash
wget "https://com-courtlistener-storage.s3-us-west-2.amazonaws.com/bulk-data/citations-2026-03-31.csv.bz2"
bunzip2 citations-2026-03-31.csv.bz2
```

Set `CITATIONS_CSV=/full/path/to/citations-2026-03-31.csv` in `.env`. See [configuration reference](configuration.md).

## Troubleshooting

- **`pip install` fails on `fast-diff-match-patch`** → [Python version notes](#python-version-notes).
- **Phase 1 returns API errors** → token missing/invalid in `.env` (`COURTLISTENER_TOKEN`).
- **`blocked` appears in results** → the opinion carries a CourtListener privacy-removal flag; Phases 2-3 are skipped by design.
- **Port already in use** → `uvicorn api:app --port 8001`.
- **Wilson says CSV is stale** → bulk data gets new snapshots periodically; the settings panel shows CSV status.
