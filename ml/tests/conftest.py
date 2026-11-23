"""Shared fixtures for the serving and monitoring tests: made-up listings and a model trained on them.

These never read data/raw, so they run the same in CI, which has no real listings.
"""

import pytest

from shotti_ml.synthetic import write_data_dir
from shotti_ml.train import train


@pytest.fixture(scope="session")
def synthetic_dir(tmp_path_factory):
    return write_data_dir(tmp_path_factory.mktemp("raw"), rows=900, seed=0)


@pytest.fixture(scope="session")
def trained(synthetic_dir, tmp_path_factory):
    """(artifact folder, metrics) for a tiny model trained with one round of 5-fold cross-validation."""
    directory, metrics, _ = train(synthetic_dir, tmp_path_factory.mktemp("artifacts"), cv_repeats=1, version="test-model")
    return directory, metrics
