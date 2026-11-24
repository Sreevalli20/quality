"""Import-integrity regression tests.

These tests exist because production once failed with
``KeyError: 'airaware.ui'``, ``KeyError: 'airaware.build_info'`` and a
``dataclasses`` ``AttributeError: 'NoneType' ...`` crash at
``sys.modules.get(cls.__module__)``. That crash only happens when a
module is executed *without* being registered in ``sys.modules`` (e.g. a
custom loader calling ``exec_module`` directly) - the standard import
system always registers a module before executing it. These tests pin
down the invariants that make the package safe: every submodule must be
importable through the normal machinery, must remain registered in
``sys.modules``, and its dataclasses must keep working across repeated
imports and Streamlit reruns.
"""

from __future__ import annotations

import importlib
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

EXPECTED_MODULES = [
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


def _fresh(code: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-c", code],
        cwd=ROOT, capture_output=True, text=True, timeout=120, check=False)


class TestFreshProcessImports:
    """Each module must import in a clean interpreter - this is what the
    deployed app actually does on cold start."""

    @pytest.mark.parametrize("mod", EXPECTED_MODULES)
    def test_module_imports_in_fresh_process(self, mod):
        proc = _fresh(f"import {mod}")
        assert proc.returncode == 0, (
            f"fresh import of {mod} failed:\n{proc.stderr}")

    def test_app_imports_in_fresh_process(self):
        proc = _fresh("import app")
        assert proc.returncode == 0, f"import app failed:\n{proc.stderr}"

    @pytest.mark.parametrize("order", [
        ["airaware.lifestyle", "airaware.pages", "airaware.ui"],
        ["airaware.ui", "airaware.build_info", "airaware.pages"],
        ["airaware.pages"] * 3,
    ])
    def test_import_order_permutations(self, order):
        stmts = "; ".join(f"import {m}" for m in order)
        proc = _fresh(f"{stmts}")
        assert proc.returncode == 0, (
            f"order {order} failed:\n{proc.stderr}")


class TestSysModulesRegistration:
    def test_all_submodules_registered_after_pages_import(self):
        importlib.import_module("airaware.pages")  # full import graph
        missing = [m for m in EXPECTED_MODULES if m not in sys.modules]
        assert not missing, f"modules missing from sys.modules: {missing}"

    def test_modules_use_standard_loaders(self):
        """Every airaware module must be a regular file loaded by the
        standard SourceFileLoader - no custom exec paths."""
        importlib.import_module("airaware.pages")  # full import graph
        for name in EXPECTED_MODULES:
            mod = sys.modules[name]
            loader_name = type(mod.__loader__).__name__
            assert loader_name == "SourceFileLoader", (
                f"{name} loaded by unexpected loader {loader_name}")
            origin = getattr(mod.__spec__, "origin", "") or ""
            assert origin.endswith(".py"), (
                f"{name} has non-file origin: {origin!r}")

    def test_no_module_shadowing(self):
        """`import airaware` must resolve to the repository package, not a
        same-named module elsewhere on sys.path."""
        import airaware
        origin = Path(airaware.__file__).resolve()
        assert origin.parent == (ROOT / "airaware").resolve()
        assert (ROOT / "airaware" / "__init__.py").exists()


class TestDataclassIntegrity:
    def test_lifestyle_option_constructs_and_inspects(self):
        from dataclasses import fields

        from airaware.lifestyle import LifestyleOption, all_options

        opt = LifestyleOption(
            area="Transport", title="t", detail="d",
            benefit="b", limitation="l")
        assert len(fields(opt)) == 7
        opts = all_options()
        assert opts and all(isinstance(o, LifestyleOption) for o in opts)

    def test_dataclasses_survive_repeated_import(self):
        lifestyle = importlib.import_module("airaware.lifestyle")

        for _ in range(2):
            importlib.reload(lifestyle)
        assert "airaware.lifestyle" in sys.modules
        opt = lifestyle.LifestyleOption(
            area="a", title="t", detail="d", benefit="b", limitation="l")
        assert opt.area == "a"

    def test_all_dataclass_modules_import_and_register(self):
        """Every module defining dataclasses must leave its classes
        introspectable - the production crash was a dataclass decorator
        failing because its module was absent from sys.modules."""
        importlib.import_module("airaware.pages")  # full import graph

        from airaware.data import MeasurementSet
        from airaware.lifestyle import LifestyleOption
        from airaware.recommendations import UserProfile

        for cls in (LifestyleOption, MeasurementSet, UserProfile):
            assert cls.__module__ in sys.modules
            assert sys.modules[cls.__module__] is not None


class TestAppStartup:
    def test_app_module_importable(self):
        import app  # noqa: F401

    def test_page_functions_all_bound(self):
        pages = importlib.import_module("airaware.pages")

        for fn in (
            "home_page", "explorer_page", "assistant_page", "planner_page",
            "indoor_page", "lifestyle_page", "impact_page",
            "community_page", "about_page",
        ):
            assert callable(getattr(pages, fn)), f"pages.{fn} missing"
