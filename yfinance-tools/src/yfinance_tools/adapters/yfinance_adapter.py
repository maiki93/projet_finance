"""
Outbound adapter:
Perform retrival of data from Yahoo Finance web site

use yfinance python library: https://ranaroussi.github.io/yfinance/
"""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

import yfinance as yf  # type: ignore

from yfinance_tools.domain import FinancialIdentifierEntry, IdentifierEntryDict
from yfinance_tools.services import YFinancePort

from .yfinance_identifier_dto import YFinanceIdentifierDto

logger = logging.getLogger(__name__)


# TODO returned type may be named from use case: IncomingIdentifierEntry Pending ...
# or directly use Pending with only incoming field
class YFinanceAdapter(YFinancePort):
    """
    Retrieval of financial data
    """

    NUM_THREADS = 5

    # name is not good / fetch_static
    # yf.Tickers([]) to consider
    def get_static_identifiers(self, ids: IdentifierEntryDict) -> IdentifierEntryDict:
        """
        Fetch yahoo finance for static data retrieval

        Request isin and fast_info (quote_type, currency)
            may split both
        """

        # perform  request : multithread version
        # needed list[ (name & yf_ticker)] name for better logging

        logger.info(f"request web fetch for: {' '.join(ids.keys())}")

        results = self.run_multithread(ids)

        # should have as much results ?
        assert len(results) == len(ids)

        static_ids = IdentifierEntryDict()
        for key, entry in results.items():
            if isinstance(entry, FinancialIdentifierEntry):
                static_ids[key] = entry

            elif isinstance(entry, str):
                logger.warning(entry)

            elif isinstance(entry, Exception):
                raise RuntimeError(f"Unexpected Error: {str(entry)}")

        return static_ids

    @classmethod
    def run_multithread(cls, ids: IdentifierEntryDict) -> dict[str, FinancialIdentifierEntry | str]:
        """ """
        with ThreadPoolExecutor(max_workers=cls.NUM_THREADS) as executor:
            future_to_key = {
                executor.submit(YFinanceAdapter.fetch_one_static_data, name, ids[name].yf_ticker): name
                for name in ids.keys()
            }

            results = {}
            # for future in as_completed(futures, timeout=30) + except TimeOutError / tqdm for progress bar
            for future in as_completed(future_to_key):
                key = future_to_key[future]  # get original key
                try:
                    # stored result or string error in future
                    results[key] = future.result()

                # it is an unexpected error
                except Exception as e:
                    # results[key] = f"Error fetching {key}: {str(e)}"
                    # results[key] = e  # str(e)
                    raise RuntimeError(e)

        return results

    # lost name asset in logs
    @staticmethod
    def fetch_one_static_data(name: str, yf_ticker: str) -> FinancialIdentifierEntry | str:

        ticker = yf.Ticker(yf_ticker)

        try:
            # fetch all, will see later for fine-grained
            ticker_isin = ticker.isin
            # lazy-loading web request on access to each attribute
            ffinfo = ticker.fast_info
            ffinfo_quote_type = ffinfo.quote_type
            ffinfo_currency = ffinfo.currency

            # all fields optional, do not raise Error
            dto = YFinanceIdentifierDto.from_fast_info(
                asset_type=ffinfo_quote_type, currency=ffinfo_currency, isin=ticker_isin
            )

            # storing yf_ticker allows to retrieve to which input it corresponds
            fin_id_entry: FinancialIdentifierEntry = YFinanceAdapter._to_domain(yf_ticker, dto)
            return fin_id_entry

        # if wrong ticker symbol, error 404 in log, but crash later in a dictionnary access
        except KeyError as ex:
            return f"Error in fetching data for {name}:{yf_ticker} KeyError: {str(ex)}"

        # potential known error, not tested
        # except yf.exceptions.YFRateLimitError as e:
        #     print("=== YFRateLimitError ===")
        #     print(str(e))
        #     return None

        # except yf.exceptions.YFException as e:
        #     print("=== YFException ===")
        #     print(str(e))
        #     return None

        except Exception as ex:
            logger.error(f"Unexpected error in YFinanceAdapter: {ex}")
            raise RuntimeError(str(ex))
            # possible safer if possible to wait for all others threads to finish work
            # return RuntimeError(ex)

    @staticmethod
    def _to_domain(yf_ticker: str, dto: YFinanceIdentifierDto) -> FinancialIdentifierEntry:
        return FinancialIdentifierEntry(
            yf_ticker=yf_ticker, asset_type=dto.asset_type, currency=dto.currency, isin=dto.isin
        )
