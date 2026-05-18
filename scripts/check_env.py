from __future__ import annotations

import importlib
import os
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
SAM3_SERVICE = ROOT / "sam3_service"


def main() -> int:
    print("== Manhua environment check ==")
    failures = 0

    failures += check_python()
    failures += check_command("node", ["node", "--version"], required=False)
    failures += check_command("npm", ["npm", "--version"], required=False)
    failures += check_imports(
        "backend deps",
        [
            "fastapi",
            "uvicorn",
            "pydantic",
            "PIL",
            "httpx",
            "dotenv",
        ],
    )
    failures += check_project_imports()
    failures += check_env_file()
    failures += check_torch()
    failures += check_sam3()

    print()
    if failures:
        print(f"Result: FAIL ({failures} problem(s))")
        return 1
    print("Result: OK")
    return 0


def check_python() -> int:
    version = sys.version_info
    conda_env = os.getenv("CONDA_DEFAULT_ENV", "")
    ok = version >= (3, 12)
    status = "OK" if ok else "FAIL"
    print(f"[{status}] python: {sys.version.split()[0]}  conda={conda_env or '-'}")
    if not ok:
        print("      Need Python 3.12+ for SAM 3.x.")
        return 1
    return 0


def check_command(name: str, cmd: list[str], required: bool) -> int:
    if shutil.which(cmd[0]) is None:
        status = "FAIL" if required else "WARN"
        print(f"[{status}] {name}: command not found")
        return 1 if required else 0
    try:
        output = subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT).strip()
        print(f"[OK] {name}: {output}")
        return 0
    except subprocess.CalledProcessError as error:
        print(f"[FAIL] {name}: {error.output.strip()}")
        return 1 if required else 0


def check_imports(label: str, modules: list[str]) -> int:
    failures = 0
    for module in modules:
        try:
            importlib.import_module(module)
            print(f"[OK] {label}: import {module}")
        except Exception as error:
            failures += 1
            print(f"[FAIL] {label}: import {module} -> {error}")
    return failures


def check_project_imports() -> int:
    failures = 0
    for label, module in [
        ("backend app", "main", BACKEND),
        ("comic pipeline", "pipeline.comic_pipeline", BACKEND),
        ("sam3 service app", "app", SAM3_SERVICE),
    ]:
        try:
            import_project_module(module, path)
            print(f"[OK] {label}: import {module}")
        except Exception as error:
            failures += 1
            print(f"[FAIL] {label}: import {module} -> {error}")
    return failures


def import_project_module(module: str, path: Path):
    old_path = sys.path[:]
    old_modules = {
        name: sys.modules.pop(name)
        for name in ["config", "main", "app"]
        if name in sys.modules
    }
    try:
        sys.path.insert(0, str(path))
        return importlib.import_module(module)
    finally:
        sys.path[:] = old_path
        for name in ["config", "main", "app"]:
            sys.modules.pop(name, None)
        sys.modules.update(old_modules)


def check_env_file() -> int:
    env_path = ROOT / ".env"
    if not env_path.exists():
        print("[WARN] .env: missing. Copy .env.example to .env before real runs.")
        return 0

    values = parse_env(env_path)
    print(f"[OK] .env: {env_path}")
    for key in [
        "USE_MOCK_PROVIDERS",
        "QWEN_BASE_URL",
        "QWEN_MODEL",
        "OPENAI_TEXT_BASE_URL",
        "OPENAI_TEXT_MODEL",
        "OPENAI_IMAGE_BASE_URL",
        "OPENAI_IMAGE_MODEL",
        "SAM3_ENDPOINT",
    ]:
        value = values.get(key, "")
        shown = "set" if value else "empty"
        print(f"     {key}: {shown}")
    return 0


def parse_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def check_torch() -> int:
    try:
        import torch
    except Exception as error:
        print(f"[WARN] torch: not installed -> {error}")
        print("       Install when you are ready for SAM3.1:")
        print('       pip install "torch>=2.7" "torchvision>=0.22" --index-url https://download.pytorch.org/whl/cu126')
        return 0

    cuda_available = torch.cuda.is_available()
    print(f"[OK] torch: {torch.__version__}")
    print(f"     cuda_available: {cuda_available}")
    if cuda_available:
        print(f"     cuda_version: {torch.version.cuda}")
        print(f"     gpu: {torch.cuda.get_device_name(0)}")
    else:
        print("     WARN: CUDA is not available. SAM3.1 will be very slow or fail if SAM3_DEVICE=cuda.")
    return 0


def check_sam3() -> int:
    try:
        importlib.import_module("sam3")
        print("[OK] sam3: import sam3")
        return 0
    except Exception as error:
        print(f"[WARN] sam3: not installed -> {error}")
        print('       Install with: pip install --upgrade "git+https://github.com/facebookresearch/sam3.git"')
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
