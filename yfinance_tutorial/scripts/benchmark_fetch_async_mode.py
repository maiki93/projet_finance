"""
Parrallelization mode to fetch data from yfinance

Parrallelization: => thread optimal ?

Session: should improve access (one TTL  handshake)


pytest-benchmark
uv run pytest scripts/benchmark_fetch_async_mode.py
"""

import argparse
import asyncio
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed

import pytest
import requests
import yfinance as yf
import yfinance.exceptions
from models import StockData

data = {
    "spaceX": {"isin": "", "yfTicker": "SPCX"},
    "quantum": {"yfTicker": "QNT", "isin": "US7479066000", "asset_type": "EQUITY"},
    "cac40": {"yfTicker": "^FCHI", "isin": "FR0003500008", "asset_type": "INDEX"},
    "eurusd": {
        "yfTicker": "EURUSD=X",
        "asset_type": "FOREX",
    },
    "bitcoin": {"yfTicker": "BTC-USD", "asset_type": "DIGITAL_ASSET"},
    "natixis": {
        "yfTicker": "0P00014IGT.F",
        "isin": "FR0011461276",
        "asset_type": "MUTUAL_FUND",
    },
    "apple": {"yfTicker": "AAPL"},
    "microsoft": {"yfTicker": "MSFT"},
    "google": {"yfTicker": "GOOG"},
    "carrefour": {"yfTicker": "CA.PA"},
}

# cache effect ?
# delete the cache before
# cache_path = "./test_cache"
# if os.path.exists(cache_path):
#    shutil.rmtree(cache_path)
# indeed call yf.cache.set_cache_location
# yf.set_tz_cache_location("./test_cache")
#
# print(f"config: {yf.config}")
# print(f"tz cache {yf.cache.get_tz_cache().initialised}")
# print(f"cache cookie: {yf.cache.get_cookie_cache().initialised}")
# print(f"isin_cache: {yf.cache.get_isin_cache().initialised}")

sem = asyncio.Semaphore(5)

g_session = None


def set_session():

    global g_session

    g_session = requests.Session()
    g_session.headers.update(
        {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
    )

    print(f"g_session: {g_session}")


def timing_decorator(func):
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        print(f"{func.__name__} executed in {(end - start) * 1e3:.2f} ms")
        return result

    return wrapper


# @timing_decorator
def update_static(stock: StockData) -> StockData | None:

    global g_session

    # no web fetch here
    yfstock = yf.Ticker(stock.yf_ticker, g_session)

    # print(f"g_session: {g_session}")
    # print(f"yfTicker.session: {yfstock.session}")
    finfo = yfstock.fast_info

    try:
        return StockData(
            stock.name,
            stock.yf_ticker,
            finfo.quote_type,
            finfo.currency,
            finfo.exchange,
            "isin",
            finfo.last_price,
        )

    except yfinance.exceptions.YFRateLimitError as e:
        print("=== YFRateLimitError ===")
        print(str(e))
        return None

    except yfinance.exceptions.YFException as e:
        print("=== YFException ===")
        print(str(e))
        return None

    except Exception as e:
        print("=== Generic Exception ===")
        print(str(e))
        return None


def run_loop_synchrone() -> list[StockData | None]:

    stocks = [update_static(StockData.from_dict(name, data)) for name in data]
    return stocks


async def limited_update(name):
    async with sem:
        return await asyncio.to_thread(update_static, StockData.from_dict(name, data))


async def loop_async() -> list[StockData | BaseException | None]:

    # update static is synchronous, must use to_thread
    tasks = [
        # asyncio.to_thread(update_static, StockData.from_dict(name, data))
        limited_update(name)
        for name in data.keys()
    ]

    # Gather Tasks: with return_exceptions=True
    # all tasks executed even if an error is encountered
    # *tasks expands the list, gather coroutines would be similar
    # advice return_exception True(default is false and dangerous)
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # print(f"Task Results: {results}")
    return results


def run_loop_asynch() -> list[StockData | BaseException | None]:
    stocks = asyncio.run(loop_async())
    return stocks


def run_loop_mthread(workers: int = 5) -> list[StockData]:  # | BaseException]: ??

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [
            executor.submit(update_static, StockData.from_dict(name, data))
            for name in data.keys()
        ]
        results = []
        for future in as_completed(futures):
            try:
                results.append(future.result())
            except Exception as e:
                results.append(e)

    return results


def run_loop_mprocess(workers: int = 5) -> list[StockData]:

    with ProcessPoolExecutor(max_workers=workers) as executor:
        futures = [
            executor.submit(update_static, StockData.from_dict(name, data))
            for name in data.keys()
        ]
        results = []
        for future in as_completed(futures):
            try:
                results.append(future.result())
            except Exception as e:
                results.append(e)

    return results


@pytest.mark.parametrize(
    "func", [run_loop_asynch, run_loop_mthread, run_loop_mprocess, run_loop_synchrone]
)
def test_info_update(benchmark, func):
    benchmark(func)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Benchmark yfinance fetching with sync or async mode"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-sync", action="store_true", help="run synchronous benchmark")
    group.add_argument(
        "-async",
        dest="async_mode",  # potential mismatch with args.async
        action="store_true",
        help="run asynchronous benchmark",
    )
    group.add_argument(
        "-mthread",
        action="store_true",
        help="run multithreaded benchmark",
    )
    group.add_argument(
        "-mprocess",
        action="store_true",
        help="run multithreaded benchmark",
    )
    # default false
    parser.add_argument(
        "-session", action="store_true", help="re-use session between calls"
    )
    args = parser.parse_args()

    use_session: bool = args.session
    if use_session:
        print("Use session")
        set_session()
    else:
        print("Do not use session")

    if args.sync:
        print("\n=====\n Sync")
        start = time.perf_counter()
        stocks = run_loop_synchrone()
        end = time.perf_counter()
        print(f"elapsed time: {round((end - start) * 1e3, 2)}")

        # for stock in stocks:
        #     print(stock)

        # print("\n== Repeat ==")
        # times = timeit.repeat(lambda: run_loop_synchrone(), number=1, repeat=1)
        # for i, t in enumerate(times, 1):
        #     print(f"Run {i}: {round(t * 1e3, 2)} ms")
        # print(f"min time: {round(min(times) * 1e3, 2)}")

    elif args.async_mode:
        print("\n=====\n Async")
        start = time.perf_counter()
        stocks = run_loop_asynch()
        end = time.perf_counter()
        print(f"elapsed time: {round((end - start) * 1e3, 2)}")

        for stock in stocks:
            print(stock)

        # print("\n== Repeat ==")
        # times = timeit.repeat(lambda: run_loop_asynch(), number=1, repeat=1)
        # for i, t in enumerate(times, 1):
        #     print(f"Run {i}: {round(t * 1e3, 2)} ms")
        # print(f"min time: {round(min(times) * 1e3, 2)}")

    elif args.mthread:
        print("\n=====\n Mutli-Threads")
        start = time.perf_counter()
        stocks = run_loop_mthread()
        end = time.perf_counter()
        print(f"elapsed time: {round((end - start) * 1e3, 2)} ms")

        # for stock in stocks:
        #    print(stock)

        # print("\n== Repeat ==")
        # times = timeit.repeat(lambda: run_loop_mthread(), number=1, repeat=1)
        # for i, t in enumerate(times, 1):
        #     print(f"Run {i}: {round(t * 1e3, 2)} ms")
        # print(f"min time: {round(min(times) * 1e3, 2)}")

    elif args.mprocess:
        print("\n=====\n Mutli-Process")
        start = time.perf_counter()
        stocks = run_loop_mprocess()
        end = time.perf_counter()
        print(f"elapsed time: {round((end - start) * 1e3, 2)} ms")

        # for stock in stocks:
        #    print(stock)

        # print("\n== Repeat ==")
        # times = timeit.repeat(lambda: run_loop_mprocess(), number=1, repeat=1)
        # for i, t in enumerate(times, 1):
        #     print(f"Run {i}: {round(t * 1e3, 2)} ms")
        # print(f"min time: {round(min(times) * 1e3, 2)}")
