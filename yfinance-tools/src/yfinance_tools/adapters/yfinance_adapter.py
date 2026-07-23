"""
Outbound adapter:
Perform retrival of data from Yahoo Finance web site

use yfinance python library: https://ranaroussi.github.io/yfinance/
"""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import cast

import yfinance as yf  # type: ignore
import yfinance.exceptions as yfexceptions  # type: ignore
from pydantic import ValidationError

from yfinance_tools.domain import FinancialIdentifierEntry, IdentifierEntryDict
from yfinance_tools.domain.exceptions import YFinanceError, YFinanceWebFetchError
from yfinance_tools.services import YFinancePort

from .yfinance_identifier_dto import YFinanceIdentifierDto

logger = logging.getLogger(__name__)


# use of internal module for better encapsulation
@dataclass(frozen=True)
class _YFFastInfo:
    quote_type: str | None
    currency: str | None
    # market / timezone data


class YFinanceAdapter(YFinancePort):
    """
    Fetch data from Yahoo Finance
    """

    NUM_THREADS = 5

    def fetch_static_identifiers(self, ids: IdentifierEntryDict) -> IdentifierEntryDict:
        """
        Fetch yahoo finance for static identifiers data retrieval
        Perform multithreaded web requests - one by asset

        Request isin and fast_info (quote_type, currency)
        """
        logger.info(f"request web fetch for: {' '.join(ids.keys())}")

        results = self._run_multithread(ids)
        # nice property to keep all entries up to here
        assert len(results) == len(ids)

        # copy validated entries, log errors
        static_ids = IdentifierEntryDict()
        for key, entry in results.items():
            if isinstance(entry, FinancialIdentifierEntry):
                static_ids[key] = entry
            else:
                logger.warning(entry)

        return static_ids

    @staticmethod
    def fetch_one_static_identifier(name: str, yf_ticker: str) -> FinancialIdentifierEntry:
        """
        Retrieve and validate static data for one asset name with yahoo ticker code
        Request isin and fast_info (quote_type, currency) - run in current thread

        Return FinancialIdentifierEntry

        Raise YFinanceError for some catched errors
        """

        _ffinfo, ticker_isin = YFinanceAdapter._fetch_isin_and_fast_info(name, yf_ticker)

        try:
            dto = YFinanceAdapter._valid_fast_info_entries(_ffinfo, ticker_isin)
        except ValidationError as ex:
            raise YFinanceError(ex)

        fin_id_entry: FinancialIdentifierEntry = YFinanceAdapter._to_domain(yf_ticker, dto)
        return fin_id_entry

    @classmethod
    def _run_multithread(cls, ids: IdentifierEntryDict) -> dict[str, FinancialIdentifierEntry | YFinanceError]:
        """ """
        with ThreadPoolExecutor(max_workers=cls.NUM_THREADS) as executor:
            future_to_key = {
                executor.submit(YFinanceAdapter.fetch_one_static_identifier, name, ids[name].yf_ticker): name
                for name in ids.keys()
            }

            # store result or catched exception at this level
            results: dict[str, FinancialIdentifierEntry | YFinanceError] = {}

            # for future in as_completed(futures, timeout=30) + except TimeOutError / tqdm for progress bar
            for future in as_completed(future_to_key):
                key = future_to_key[future]  # get original key
                try:
                    results[key] = future.result()
                except YFinanceError as ex:
                    results[key] = ex
                # else will crash (eg: RuntimeError)

        return results

    @staticmethod
    def _fetch_isin_and_fast_info(name: str, yf_ticker: str) -> tuple[_YFFastInfo, str]:
        """
        Perform the web request
        Good candidate for mock in unit-test

        Raise YFinanceWebFetchError by catchting all yfinance.exceptions.YFException
        """
        ticker = yf.Ticker(yf_ticker)
        try:
            # fetch all, will see later for fine-grained
            ticker_isin = ticker.isin
            # lazy-loading web request on access to each attribute
            ffinfo = ticker.fast_info
            ffinfo_quote_type = ffinfo.quote_type
            ffinfo_currency = ffinfo.currency

        # if wrong ticker symbol, error 404 in log, but crash later in a dictionnary access
        except KeyError as ex:
            raise YFinanceWebFetchError(f"Error in fetching data for {name}:{yf_ticker} KeyError: {str(ex)}")

        # multiple errors may appear from yfinance specifically
        # if catched and rethrow as YFinanceError will not stop of the multithread command
        except (yfexceptions.YFRateLimitError, yfexceptions.YFException) as ex:
            raise YFinanceWebFetchError(ex)

        return _YFFastInfo(ffinfo_quote_type, ffinfo_currency), cast(str, ticker_isin)

    @staticmethod
    def _valid_fast_info_entries(yfinfo: _YFFastInfo, isin: str | None) -> YFinanceIdentifierDto:
        """Entries are validated with DTO"""
        return YFinanceIdentifierDto.model_validate(
            {"asset_type": yfinfo.quote_type, "currency": yfinfo.currency, "isin": isin}
        )

    @staticmethod
    def _to_domain(yf_ticker: str, dto: YFinanceIdentifierDto) -> FinancialIdentifierEntry:
        return FinancialIdentifierEntry(
            yf_ticker=yf_ticker, asset_type=dto.asset_type, currency=dto.currency, isin=dto.isin
        )
