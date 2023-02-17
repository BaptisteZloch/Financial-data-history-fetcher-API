from datetime import datetime
from typing import Optional
import os
import pandas as pd
from src.services.service import Service
from src.modules.kucoin_fetcher import KucoinDataFetcher


class CryptoService(Service):
    __kucoin_fetcher = KucoinDataFetcher()
    __base_dir = "./database/"
    __absolute_start_date = "01-01-2017"

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

    def __refresh_or_download(self, symbol, timeframe) -> pd.DataFrame:
        if os.path.exists(f"{self.__base_dir}{timeframe}/{symbol}.csv"):
            print("History present -> Checking for refresh...")
            data = pd.read_csv(f"{self.__base_dir}{timeframe}/{symbol}.csv", sep=",")
            last_timestamp = data["Timestamp"].iloc[-1]

            since = datetime.fromtimestamp(last_timestamp).strftime("%d-%m-%Y")
            print(f"Last timestamp : {last_timestamp} = {since}")
            if since == datetime.now().strftime("%d-%m-%Y"):
                return data
            new_data = self.__kucoin_fetcher.download_history(
                symbol, since, timeframe, 16
            )

            data = pd.concat([data, new_data]).drop_duplicates(ignore_index=True)
            data.to_csv(
                f"{self.__base_dir}{timeframe}/{symbol}.csv", sep=",", index=False
            )
            return data
        else:  # Download full history
            print("No history -> Downloading full history...")
            data = self.__kucoin_fetcher.download_history(
                symbol, self.__absolute_start_date, timeframe, 16
            )
            data.to_csv(
                f"{self.__base_dir}{timeframe}/{symbol}.csv", sep=",", index=False
            )
            return data

    def get_history_of_symbol(self, symbol: str, timeframe: str) -> list[dict]:
        assert (
            timeframe in self.__kucoin_fetcher.timeframes
        ), f"Error, timeframe must be in {self.__kucoin_fetcher.timeframes}"

        return self.__refresh_or_download(symbol, timeframe).to_dict(orient="records")

        # assert (
        #     symbol in self.__kucoin_fetcher.get_symbols()
        # ), "Error, wrong symbol, provide something like 'BTC-USDT'."
