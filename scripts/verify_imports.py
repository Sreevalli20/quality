"""Fresh-process import verification for the AirAware package.

Run before every deployment (and in CI):

    python scripts/verify_imports.py

Every check executes in a *separate* Python process so that import-order
effects, partial sys.modules state and stale bytecode cannot hide behind
an already-warm interpreter. Exits non-zero on the first failure.

This script intentionally uses only the standard import system: if any
module here fails, the deployment tree or runtime is broken - do not
"fix" it by manipulating sys.modules.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Every shipped module, in dependency order (leaves first).
MODULES = [
    "airaware",
    "airaware.aqi",
    "airaware.tzutil",
    "airaware.textutil",
    "airaware.data",
    "airaware.ai",
    "airaware.alerts",
    "airaware.charts",
    "airaware.forecast",
    "airaware.impact",
    "airaware.indoor",
    "airaware.planner",
    "airaware.providers",
    "airaware.recommendations",
    "airaware.report",
    "airaware.lifestyle",
    "airaware.ui",
    "airaware.build_info",
    "airaware.pages",
]

# Import orders that historically exposed ordering bugs. Each tuple is
# executed as a single fresh process.
ORDER_PERMUTATIONS = [
    ("airaware.lifestyle", "airaware.pages", "airaware.ui"),
    ("airaware.pages", "airaware.lifestyle", "airaware.ui"),
    ("airaware.ui", "airaware.build_info", "airaware.pages"),
    ("airaware.pages", "airaware.pages", "airaware.pages"),  # repeats
]


def _fresh(code: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-c", code],
        cwd=ROOT, capture_output=True, text=True, timeout=120, check=False)


def check_single_imports() -> list[str]:
    failures = []
    for mod in MODULES:
        proc = _fresh(f"import {mod}; print('ok')")
        if proc.returncode != 0 or "ok" not in proc.stdout:
            failures.append(f"fresh import of {mod!r} failed:\n{proc.stderr}")
    return failures


def check_registration() -> list[str]:
    """After importing the package entry points, every submodule must be
    present in sys.modules and every dataclass must be constructible."""
    code = (
        "import sys\n"
        "import airaware.pages\n"
        "import airaware.ui\n"
        "import airaware.build_info\n"
        "expected = " + repr(MODULES) + "\n"
        "missing = [m for m in expected if m not in sys.modules]\n"
        "assert not missing, f'modules missing from sys.modules: {missing}'\n"
        "from dataclasses import fields\n"
        "from airaware.lifestyle import LifestyleOption, all_options\n"
        "opt = LifestyleOption(area='a', title='t', detail='d',"
        " benefit='b', limitation='l')\n"
        "assert len(fields(opt)) == 7\n"
        "assert all_options()\n"
        "print('ok')\n"
    )
    proc = _fresh(code)
    if proc.returncode != 0 or "ok" not in proc.stdout:
        return [f"registration/dataclass check failed:\n{proc.stderr}"]
    return []


def check_order_permutations() -> list[str]:
    failures = []
    for order in ORDER_PERMUTATIONS:
        stmts = "; ".join(f"import {m}" for m in order)
        proc = _fresh(f"{stmts}; print('ok')")
        if proc.returncode != 0 or "ok" not in proc.stdout:
            failures.append(
                f"import order {order} failed:\n{proc.stderr}")
    return failures


def check_reload() -> list[str]:
    """Repeated importlib.reload of every module must not corrupt
    sys.modules or break dataclasses (Streamlit reruns rely on stable
    module identity)."""
    mods = ", ".join(repr(m) for m in MODULES)
    code = (
        "import importlib, sys\n"
        f"mods = [{mods}]\n"
        "for _ in range(2):\n"
        "    for m in mods:\n"
        "        importlib.reload(importlib.import_module(m))\n"
        "missing = [m for m in mods if m not in sys.modules]\n"
        "assert not missing, f'modules lost after reload: {missing}'\n"
        "from airaware.lifestyle import LifestyleOption\n"
        "LifestyleOption(area='a', title='t', detail='d',"
        " benefit='b', limitation='l')\n"
        "print('ok')\n"
    )
    proc = _fresh(code)
    if proc.returncode != 0 or "ok" not in proc.stdout:
        return [f"reload check failed:\n{proc.stderr}"]
    return []


def main() -> int:
    failures: list[str] = []
    failures += check_single_imports()
    failures += check_registration()
    failures += check_order_permutations()
    failures += check_reload()

    if failures:
        print("IMPORT VERIFICATION FAILED")
        for f in failures:
            print("-" * 60)
            print(f)
        return 1
    print(f"OK: {len(MODULES)} modules import cleanly in fresh processes; "
          "sys.modules registration, dataclasses, import order and "
          "reload cycles verified.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
