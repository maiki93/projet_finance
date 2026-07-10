"""
Benchmark the 3 options to retrieve static and last values

I guess same problem of cached data

need pytest-banchmark

uv run pytest scripts/benchamark_static_and_last_values.py --benchmark-verbose

"""

import pytest
import yfinance as yf

# from pytest_benchmark.fixture import benchmark
from models import StockData

data = {
    "spaceX": {"isin": "", "yfTicker": "SPCX"},
    "cac40": {"yfTicker": "^FCHI", "isin": "FR0003500008", "asset_type": "INDEX"},
    "quantum": {"yfTicker": "QNT", "isin": "US7479066000", "asset_type": "EQUITY"},
    "eurusd": {
        "yfTicker": "EURUSD=X",
        "asset_type": "FOREX",
    },
    "bitcoin": {"yfTicker": "BTC-USD", "asset_type": "DIGITAL_ASSET"},
    "oil_wti": {"yfTicker": "CL=F"},
    "oil_brent": {"yfTicker": "BZ=F"},
    "oil_brent2": {"yfTicker": "BZU26.NYM"},  # underlying: BZ.NYM
}


#
def update_static_fast_info(stock: StockData):
    ticker = yf.Ticker(stock.yf_ticker)
    # lazy-loading: no http  executed
    # always 20 keys, fetched on access
    finfo = ticker.fast_info
    # try / catch
    return StockData(
        stock.name, stock.yf_ticker, finfo.quote_type, finfo.currency, finfo.exchange
    )


def update_static_info(stock: StockData):
    ticker = yf.Ticker(stock.yf_ticker)
    # perform all web requests
    info = ticker.info
    # try / catch
    return StockData(
        stock.name,
        stock.yf_ticker,
        info["quoteType"],
        info["currency"],
        info["exchangeTimezoneName"],
    )


def update_last_price_fast_info(stock: StockData):
    ticker = yf.Ticker(stock.yf_ticker)
    # lazy-loading: no http  executed
    # always 20 keys, fetched on access
    finfo = ticker.fast_info
    # try / catch
    return StockData(stock.name, stock.yf_ticker, last_price=finfo.last_price)


def update_last_price_info(stock: StockData):
    ticker = yf.Ticker(stock.yf_ticker)
    # perform all web requests
    info = ticker.info
    # try / catch
    return StockData(stock.name, stock.yf_ticker, last_price=info["regularMarketPrice"])


def update_last_price_histo_meta(stock: StockData):
    ticker = yf.Ticker(stock.yf_ticker)
    # perform all web requests
    meta_h = ticker.get_history_metadata()
    # try / catch
    return StockData(
        stock.name, stock.yf_ticker, last_price=meta_h["regularMarketPrice"]
    )


#
# Tests
#


# if first, show a bigger max (160ms)
@pytest.mark.parametrize("func", [update_static_info, update_last_price_info])
def test_info_update(benchmark, func):
    stock = StockData.from_dict("cac40", data)
    benchmark(func, stock)


@pytest.mark.parametrize("func", [update_static_fast_info, update_last_price_fast_info])
def test_fast_info_update(benchmark, func):
    stock = StockData.from_dict("spaceX", data)
    benchmark(func, stock)  # warmup only in pedantic mode


@pytest.mark.parametrize("func", [update_last_price_histo_meta])
def test_histo_meta_update(benchmark, func):
    stock = StockData.from_dict("eurusd", data)
    benchmark(func, stock)
