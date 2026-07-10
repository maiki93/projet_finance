"""
To monitor the http requests when fetching data:
- static_data: market, exchange, currency...
- last values: last price, date, ...

Multiple options to retrieve those data:
1. Quote.info, available by Ticker._quote.info (+ 100 keys)
    Always 3 web (spaceX), done at `ticker.info` command
    - Only one to show Sector/Industry (equity specific ?)

2. PriceHistory: access by Ticker.get_historic_metadata() ~ 30 entries : 1 request
    assec by Ticker._price_history, retrieve only a few days

3. FastInfo: Ticker._fast_info (always 20 fixed entries), up to 4 web requests
    lazy-loading: web request on attribute access

By activacting the debug mode of yfinance, it is possible to follow the different calls
in the log file

!! The order is important !!
If fast_info is loaded before historic_metadata, only 26 entries are retrieved (no lastPrice) ??

uv run --with scalene scalene run scripts/fetch_static_and_last_values.py
uv run --with scalene scalene view scalene-profile.json
"""

import argparse
import logging
import time
from datetime import datetime
from zoneinfo import ZoneInfo

import yfinance as yf

# all yfinance debugging, print to stdout by default
# keep False to disable the console output,
#   but will be redirected to file if a root logger is defined
yf.config.debug.logging = False
# set to False to stop yfinance hiding exceptions.
yf.config.debug.hide_exceptions = False

logger = logging.getLogger(__name__)


def timing_decorator(func):
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        print(f"{func.__name__} executed in {(end - start) * 1e3:.2f} ms")

        if logger.isEnabledFor(logging.DEBUG):
            logger.info(f"{func.__name__} executed in {(end - start) * 1e3:.2f} ms")
        return result

    return wrapper


def setup_logging():
    """
    Definition of a root logger
    Yfinance debug messages will be redirected to the file
    """
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler("debug_script.log")],
        # force=True
    )


def yf_config():
    """Configuration"""
    print("yf.config:")
    print(yf.config)


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
    "oil_brent": {
        "yfTicker": "BZ=F"
    },  # show FUTURE, underlyingSymbol: BZU26.NYM, shortName: Brent Crude Oil Last Day Financ
    "oil_brent2": {"yfTicker": "BZU26.NYM"},  # underlying: BZ.NYM
    # "oil_brent3": {"yfTicker": "BZ.NYM"}, error (404)
}


# quote.py::FastInfo, stored in Ticker._fast_info, full lazy-loading (depends on each key)
# may aslo call history_metadata
# Up to 4 http requests:
# ticker.get_history_metadata (period="5d")
# + self._tkr.history(period="1y", auto_adjust=False, keepna=True)
@timing_decorator
def print_fast_info(ticker: yf.Ticker, details: bool = False):

    # lazy-loading: no http  executed, nb keys always 20
    finfo = ticker.fast_info
    print(f"fast_info, nb entries {len(finfo.keys())}")
    logger.debug(f"fast_info, nb entries {len(finfo.keys())}")

    # 4 web calls (more than info)
    if details:
        for key, value in finfo.items():
            print(f"  {key}: {value}")

    else:
        # 1 call only: get_history_metadata()
        print(
            f"quoteType: {finfo.quote_type}"
        )  # <=> finfo.quote_type, finfo.get("quoteType")
        print(f"currency: {finfo['currency']}")
        # 2nd call
        print(f"exchange: {finfo['exchange']}")  # NMS
        print(f"lastPrice: {finfo['lastPrice']}")
        print(f"timezone: {finfo['timezone']}")
        # logger.debug("==test==")
        print(f"lastVolume: {finfo['lastVolume']}")
        print(f"open: {finfo.open}")
        # no access to
        # ... depends on key up to 4 calls


# PriceHistory (history.py)
# Sometimes 26, sometimes 30 entries ?? lastTrade, previousClose, (tradingPeriods, scale ??)...
# If Fast info is called before => 26 entries
# else  => 30 entries (scale: 3, priceHint: 2)
#
# Only 1 web call:
# url=https://query2.finance.yahoo.com/v8/finance/chart/SPCX
# params={'range': '5d', 'interval': '1h', 'includePrePost': True, 'events': 'div,splits,capitalGains'}
@timing_decorator
def print_historic_metadata(ticker: yf.Ticker, details: bool = False):

    # perform the request
    h_meta = ticker.get_history_metadata()  # option repair

    # 30 entries (if called first, before fast_info ?)
    print(f"historic metadata nb entries: {len(h_meta)}")
    logger.debug(f"historic_metadata, nb entries {len(h_meta.keys())}")

    if details:
        for key, value in h_meta.items():
            print(f"  {key}: {value}")
    else:
        print(f"symbol: {h_meta['symbol']}")
        print(f"longName: {h_meta['longName']}")
        # more exchange: exchangeName: NMS, fullExchangeName: NasdaqGS, exchangeTimezoneName: America/New_York
        # timezone: EDT
        print(f"gmtoffset: {h_meta['gmtoffset']}")
        # regularMarketDayHigh: 162.16, regularMarketDayLow: 155.88, regularMarketVolume: 60289936
        print(f"regularMarketPrice: {h_meta['regularMarketPrice']}")
        print(f"regularMarketTime: {h_meta['regularMarketTime']}")
        # unix timestamp ??
        # inside code utils.py (907) format_history_metadata
        # tz= md["exchangeTimezoneName"]
        # ... and if "regularMarketTime"
        # md[k] = _pd.to_datetime(md[k], unit='s', utc=True).tz_convert(tz)
        market_time = h_meta["regularMarketTime"]
        # Convert to datetime (local time)
        dt = datetime.fromtimestamp(market_time)
        formatted_date = dt.strftime("%Y-%m-%d %H:%M:%S")
        print(f"regularMarketTime (local) : {formatted_date}")

        # standard python
        dt = datetime.fromtimestamp(market_time, tz=ZoneInfo("UTC"))
        dt_ny = dt.astimezone(ZoneInfo("America/New_York"))
        print(f"regularMarketTime (new york) : {dt_ny}")
        #
        if h_meta.get("previousClose"):
            print(f"previous close: {h_meta['previousClose']} ")
        if h_meta.get("lastTrade"):
            print(f"lastTrade: {h_meta['lastTrade']}")


# call Quote Ticker._quote.info
# 3 web calls (spaceX) - 2 calls oil (FUTURE): whatever the required attributes
# - url=https://query2.finance.yahoo.com/v10/finance/quoteSummary/SPCX
#   params={'modules': 'financialData,quoteType,defaultKeyStatistics,assetProfile,summaryDetail', 'corsDomain': 'finance.yahoo.com', 'formatted': 'false', 'symbol': 'SPCX', 'lang': 'en-US', 'region': 'US'}
# - url=https://query1.finance.yahoo.com/v7/finance/quote?
#   params={'symbols': 'SPCX', 'formatted': 'false', 'lang': 'en-US', 'region': 'US'}
# for equity, not for future
# - url=https://query1.finance.yahoo.com/ws/fundamentals-timeseries/v1/finance/timeseries/SPCX?symbol=SPCX&type=trailingPegRatio&period1=1767657600&period2=1783468800
#   params=None
#
# nb entries (spaceX: 149) =
#            oil: 73       = 16 ms !! much faster ONLY if details = True !! some data have been cached ... really not clear
@timing_decorator
def print_info(ticker: yf.Ticker, details=True):

    # perform all web requests
    start = time.perf_counter()
    info = ticker.info
    end = time.perf_counter()
    print(f"time fetch: {(end - start) * 1e3:.2f} ms")
    logger.debug(f"time fetch: {(end - start) * 1e3:.2f} ms")

    print(f"info nb entries: {len(info)}")
    logger.debug(f"info (full), nb entries {len(info.keys())}")

    if details:
        for key, value in info.items():
            print(f"  {key}: {value}")

    # much longer because copies are done ?
    else:
        print(f"longName: {info['longName']}")
        print(f"shortName: {info['shortName']}")
        print(f"quoteType: {info['quoteType']}")
        print(f"currency: {info['currency']}")
        print(f"marketState: {info['marketState']}")
        print(f"regularMarketPrice: {info['regularMarketPrice']}")
        ## allTimeHigh, allTimeLow
        print(f"open: {info['open']}")
        print(f"regularMarketTime: {info['regularMarketTime']}")
        print(f"regularMarketChangePercent: {info['regularMarketChangePercent']}")
        ## exchange: NYM, exchangeTimezoneName: America/New_York, exchangeTimezoneShortName: EDT
        print(f"exchangeTimezoneName: {info['exchangeTimezoneName']}")


def main(all_keys: bool = False):

    logger.info("Entry script")

    # to extend, create generator with random order
    symbols = ["oil_brent2", "cac40", "eurusd"]

    print(f"== create Ticker : {symbols[0]}")
    # never web request done at initialization
    # Session associated to the ticker
    ticker = yf.Ticker(data[symbols[0]]["yfTicker"])
    session1 = ticker.session
    # assert ticker.session is None
    # ask isin creates a first call
    # print(f"isin: {ticker.isin}")

    print("\n== load history_metadata")
    # recreate each time to force a new session
    ticker = yf.Ticker(data[symbols[0]]["yfTicker"])
    assert ticker.session != session1
    print_historic_metadata(ticker, details=all_keys)

    print("\n == load fast_info")
    ticker = yf.Ticker(data[symbols[1]]["yfTicker"])
    print_fast_info(ticker, details=all_keys)

    print("\n== load info (full)")
    ticker3 = yf.Ticker(data[symbols[2]]["yfTicker"])
    print_info(ticker3, details=all_keys)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-d", "--debug", action="store_true", help="activate logfile script + yfinance"
    )
    parser.add_argument(
        "-a",
        "--all",
        action="store_true",
        help="print all keys/values, or only pre-defined",
    )
    args = parser.parse_args()
    # activate debug log file (script + yfinance debug)
    if args.debug:
        setup_logging()

    yf_config()

    main(all_keys=args.all)
