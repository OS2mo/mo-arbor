# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
import json

import pytest
from pytest import Item
from pytest import MonkeyPatch


@pytest.hookimpl(trylast=True)
def pytest_collection_modifyitems(items: list[Item]) -> None:
    """Fake `autouse` fixtures for tests marked with integration_test.

    Uses trylast=True so it runs after the fastramqpi plugin's hook, ensuring
    our prepended fixtures end up before the plugin's fixtures.
    """
    for item in items:
        if item.get_closest_marker("integration_test"):
            # MUST prepend to replicate auto-use fixtures coming first
            item.fixturenames[:0] = [  # type: ignore[attr-defined]
                "integration_test_environment_variables",
            ]


@pytest.fixture
def integration_test_environment_variables(monkeypatch: MonkeyPatch) -> None:
    """Default environment for integration tests.

    Automatically used by tests marked 'integration_test' (see
    pytest_collection_modifyitems). A test can override it with
    @pytest.mark.envvar.
    """
    monkeypatch.setenv(
        "CODE_SYSTEMS",
        json.dumps(["sor", "okosted"]),
    )


@pytest.fixture
def minimal_valid_environmental_variables(monkeypatch: MonkeyPatch) -> None:
    """What FastRAMQPI's settings require, for tests of the settings."""
    monkeypatch.setenv("FASTRAMQPI__CLIENT_ID", "mo-arbor")
    monkeypatch.setenv("FASTRAMQPI__CLIENT_SECRET", "secret")
