"""Fixtures for the integration tests.

The tests need the packages from requirements_dev.txt and run with Python 3.14 (the version
required by pytest-homeassistant-custom-component for the current Home Assistant release).
"""
import pytest


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Allow Home Assistant to load the integration from custom_components/."""
    yield
