"""Unit tests for the SQLite-backed IC diffusion configuration."""

import pytest

from im_research.core import diffusion_config as dc


@pytest.fixture
def isolated_db(tmp_path, monkeypatch):
    monkeypatch.setattr(dc, "DB_PATH", tmp_path / "config.db")
    return tmp_path / "config.db"


def test_defaults_are_returned_when_db_is_empty(isolated_db):
    config = dc.get_ic_config()
    assert config["model"] == "IC"
    assert config["probability_mode"] == "uniform"
    assert config["edge_probability"] == 0.1
    assert config["mc_search"] == 200
    assert config["mc_validation"] == 1000
    assert config["seed_search"] == 42
    assert config["seed_validation"] == 12345


def test_save_and_reload(isolated_db):
    saved = dc.save_ic_config(
        {
            "model": "IC",
            "probability_mode": "uniform",
            "edge_probability": "0,15",
            "mc_search": "250",
            "mc_validation": "2000",
            "seed_search": "7",
            "seed_validation": "999",
        }
    )
    assert saved["edge_probability"] == 0.15
    assert saved["mc_search"] == 250

    loaded = dc.get_ic_config()
    assert loaded == saved


def test_reset_restores_defaults(isolated_db):
    dc.save_ic_config(
        {
            "edge_probability": "0.3",
            "mc_search": "500",
            "mc_validation": "5000",
            "seed_search": "1",
            "seed_validation": "2",
        }
    )
    reset = dc.reset_ic_config()
    assert reset == dc.DEFAULT_IC_CONFIG
    assert dc.get_ic_config() == dc.DEFAULT_IC_CONFIG


@pytest.mark.parametrize(
    "overrides, message",
    [
        ({"model": "LT"}, "Independent Cascade"),
        ({"probability_mode": "weighted"}, "Uniform"),
        ({"edge_probability": "0"}, "Xác suất cạnh p"),
        ({"edge_probability": "1.1"}, "Xác suất cạnh p"),
        ({"mc_search": "0"}, "Số lần mô phỏng MC"),
        ({"mc_validation": "abc"}, "Số lần mô phỏng MC"),
        ({"seed_search": "-1"}, "Seed evaluator"),
    ],
)
def test_invalid_values_are_rejected(isolated_db, overrides, message):
    with pytest.raises(ValueError, match=message):
        dc.save_ic_config({**dc.DEFAULT_IC_CONFIG, **overrides})
