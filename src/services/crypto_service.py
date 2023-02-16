from datetime import datetime
from typing import Optional
import os
import pandas as pd
from src.services.service import Service
from src.modules.kucoin_fetcher import KucoinDataFetcher


class CryptoService(Service):
    __kucoin_fetcher = KucoinDataFetcher()
    __base_dir = "../../database/"

    def get_list_of_symbols(
        self, base_currency: Optional[str], quote_currency: Optional[str]
    ) -> list[str]:
        if base_currency == None and quote_currency == None:
            return self.__kucoin_fetcher.get_symbols()
        elif base_currency == None and quote_currency is not None:
            return list(
                filter(
                    lambda symbol: symbol.split("-")[-1] == quote_currency.upper(),
                    self.__kucoin_fetcher.get_symbols(),
                )
            )
        elif quote_currency == None and base_currency is not None:
            return list(
                filter(
                    lambda symbol: symbol.split("-")[0] == base_currency.upper(),
                    self.__kucoin_fetcher.get_symbols(),
                )
            )
        elif quote_currency is not None and base_currency is not None:
            return list(
                filter(
                    lambda symbol: symbol.split("-")[0] == base_currency.upper()
                    and symbol.split("-")[-1] == quote_currency.upper(),
                    self.__kucoin_fetcher.get_symbols(),
                )
            )
        raise ValueError("Error, wrong parameters.")

    def __check_and_refresh(self, symbol, timeframe, since: str):
        if os.path.exists(f"{self.__base_dir}{timeframe}/{symbol}.csv"):
            data = pd.read_csv(f"{self.__base_dir}{timeframe}/{symbol}.csv")
        else:
            self.__kucoin_fetcher.download_history(symbol, since, timeframe, 16)

    def get_history_of_symbol(
        self, symbol: str, timeframe: str, since: str | None = None
    ):
        assert (
            timeframe in self.__kucoin_fetcher.timeframes
        ), f"Error, timeframe must be in {self.__kucoin_fetcher.timeframes}"
        if since is not None:
            try:
                start_timestamp = int(datetime.strptime(since, "%d-%m-%Y").timestamp())
            except:
                raise ValueError(
                    "Error, wrong date format, provide something in this format: dd-mm-yyyy"
                )

        # assert (
        #     symbol in self.__kucoin_fetcher.get_symbols()
        # ), "Error, wrong symbol, provide something like 'BTC-USDT'."
