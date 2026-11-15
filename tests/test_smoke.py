"""Smoke tests: every CLI module imports and every command answers --help (no network)."""

import importlib
import pkgutil

import pytest
from click.testing import CliRunner

import ic.cli
from ic.ic import main

CLI_MODULES = [m.name for m in pkgutil.iter_modules(ic.cli.__path__)]


@pytest.mark.parametrize("name", CLI_MODULES)
def test_import_cli_module(name):
    importlib.import_module(f"ic.cli.{name}")


def test_main_help():
    result = CliRunner().invoke(main, ["--help"])
    assert result.exit_code == 0, result.output


@pytest.mark.parametrize("command", sorted(main.commands))
def test_subcommand_help(command):
    result = CliRunner().invoke(main, [command, "--help"])
    assert result.exit_code == 0, result.output
    assert "Usage" in result.output
