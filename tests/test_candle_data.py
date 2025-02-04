"""Synthetic candle data tests."""

import pandas as pd
import pytest

from tradingstrategy.candle import Candle, GroupedCandleUniverse, CandleSampleUnavailable


@pytest.fixture()
def synthetic_candles() -> pd.DataFrame:
    """Some hand-written test data.

    Contains candle data for one trading pair (pair_id=1)
    """

    data = [
        Candle.generate_synthetic_sample(1, pd.Timestamp("2020-01-01"), 100.10),
        Candle.generate_synthetic_sample(1, pd.Timestamp("2020-02-01"), 100.50),
        Candle.generate_synthetic_sample(1, pd.Timestamp("2020-03-01"), 101.10),
        Candle.generate_synthetic_sample(1, pd.Timestamp("2020-09-01"), 101.80),
    ]

    df = pd.DataFrame(data, columns=Candle.DATAFRAME_FIELDS)
    return df


def test_generate_candle_data(synthetic_candles):
    """Test creation of candles."""

    universe = GroupedCandleUniverse(synthetic_candles)

    assert universe.get_pair_count() == 1
    assert universe.get_candle_count() == 4

    df = universe.get_candles_by_pair(pair_id=1)
    assert df.loc[pd.Timestamp("2020-01-01")]["open"] == pytest.approx(100.10)
    assert df.loc[pd.Timestamp("2020-02-01")]["close"] == pytest.approx(100.50)


def test_get_price_with_tolerance(synthetic_candles):
    """Correctly get a price within a tolerance."""

    universe = GroupedCandleUniverse(synthetic_candles)
    assert universe.get_pair_count() == 1
    assert universe.get_candle_count() == 4

    test_price, distance = universe.get_price_with_tolerance(pair_id=1, when=pd.Timestamp("2020-01-01"), tolerance=pd.Timedelta(1, "d"))
    assert test_price == pytest.approx(100.10)
    assert distance == pd.Timedelta(0)

    test_price, distance = universe.get_price_with_tolerance(pair_id=1, when=pd.Timestamp("2020-01-02"), tolerance=pd.Timedelta(1, "d"))
    assert test_price == pytest.approx(100.10)
    assert distance == pd.Timedelta("1d")

    test_price, distance = universe.get_price_with_tolerance(pair_id=1, when=pd.Timestamp("2020-02-01"), tolerance=pd.Timedelta(1, "m"))
    assert test_price == pytest.approx(100.50)
    assert distance == pd.Timedelta(0)

    test_price, distance = universe.get_price_with_tolerance(pair_id=1, when=pd.Timestamp("2020-02-01 00:05"), tolerance=pd.Timedelta(30, "m"))
    assert test_price == pytest.approx(100.50)
    assert distance == pd.Timedelta("5m")


def test_get_price_not_within_tolerance(synthetic_candles):
    """Test creation of candles."""

    universe = GroupedCandleUniverse(synthetic_candles)

    with pytest.raises(CandleSampleUnavailable):
        universe.get_price_with_tolerance(
            pair_id=1,
            when=pd.Timestamp("2020-01-05"),
            tolerance=pd.Timedelta(1, "d"))

    with pytest.raises(CandleSampleUnavailable):
        universe.get_price_with_tolerance(
            pair_id=1,
            when=pd.Timestamp("2020-01-01 00:05"),
            tolerance=pd.Timedelta(1, "m"))


def test_get_single_pair_data_allow_current(synthetic_candles):
    """Check for our forward-looking bias mitigation."""

    universe = GroupedCandleUniverse(synthetic_candles)

    candles = universe.get_single_pair_data(timestamp=pd.Timestamp("2020-09-01"))
    assert candles.iloc[-1]["timestamp"] == pd.Timestamp("2020-03-01")

    candles = universe.get_single_pair_data(timestamp=pd.Timestamp("2020-09-01"), allow_current=True)
    assert candles.iloc[-1]["timestamp"] == pd.Timestamp("2020-09-01")
