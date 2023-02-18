from datetime import datetime
from typing import Optional
import os
import pandas as pd
import json

from src.services.service import Service
from src.modules.kucoin_fetcher import KucoinDataFetcher


class CryptoService(Service):
    __kucoin_fetcher = KucoinDataFetcher()
    __base_dir = (
        "./database/"
        if os.getenv("APP_ENV", "dev") == "dev"
        else "/usr/src/app/database/"
    )
    __absolute_start_date = "01-01-2017"

    def get_list_of_symbols(
        self, base_currency: Optional[str] = None, quote_currency: Optional[str] = None
    ) -> list[str]:
        """Return the list of symbol in the database's file.

        Args:
            base_currency (Optional[str]): Filter by base currency.
            quote_currency (Optional[str]): Filter by quote currency.

        Raises:
            ValueError: If there is an error.

        Returns:
            list[str]: The list of symbols.
        """
        symbols = self.__open_symbols_list()
        if base_currency == None and quote_currency == None:
            return symbols
        elif base_currency == None and quote_currency is not None:
            return list(
                filter(
                    lambda symbol: symbol.split("-")[-1] == quote_currency.upper(),
                    symbols,
                )
            )
        elif quote_currency == None and base_currency is not None:
            return list(
                filter(
                    lambda symbol: symbol.split("-")[0] == base_currency.upper(),
                    symbols,
                )
            )
        elif quote_currency is not None and base_currency is not None:
            return list(
                filter(
                    lambda symbol: symbol.split("-")[0] == base_currency.upper()
                    and symbol.split("-")[-1] == quote_currency.upper(),
                    symbols,
                )
            )
        raise ValueError("Error, wrong parameters.")

    def get_history_of_symbol(
        self, symbol: str, timeframe: str
    ) -> list[dict[str, float | int]]:
        """Function that get the history of a symbol.

        Args:
            symbol (str): The crypto symbol file.
            timeframe (str): The history's timeframe.

        Returns:
            list[dict[str, float | int]]: The list of record corresponding to the history.
        """
        assert (
            timeframe in self.__kucoin_fetcher.timeframes
        ), f"Error, timeframe must be in {self.__kucoin_fetcher.timeframes}"

        assert (
            symbol in self.get_list_of_symbols()
        ), "Error, wrong symbol, provide something like 'BTC-USDT'."

        return self.__refresh_or_download(symbol, timeframe).to_dict(orient="records")

    def refresh_list_of_symbols(self) -> None:
        """Function that refreshes the database's crypto listing."""
        self.__init_directories()
        with open(f"{self.__base_dir}list_available/crypto_available.json", "w") as f:
            json.dump({"listing": self.__kucoin_fetcher.get_symbols()}, f)

    def check_file_exists(self, symbol: str, timeframe: str) -> bool:
        """Verify if the history has already been fetched

        Args:
            symbol (str): The crypto symbol file.
            timeframe (str): The history's timeframe.

        Returns:
            bool: Whether or not the history is present.
        """
        return os.path.exists(f"{self.__base_dir}{timeframe}/{symbol}.csv")

    def __open_symbols_list(self) -> list[str]:
        """Private function that opens, reads and returns the list of symbols from the database's file.

        Returns:
            list[str]: The list of symbols.
        """
        with open(f"{self.__base_dir}list_available/crypto_available.json", "r") as f:
            return json.load(f)["listing"]

    def __refresh_or_download(self, symbol: str, timeframe: str) -> pd.DataFrame:
        """Private function used to refresh or download the history of a symbol.

        Args:
            symbol (str): The crypto symbol file.
            timeframe (str): The history's timeframe.

        Returns:
            pd.DataFrame: The complete history refreshed or not.
        """
        if self.check_file_exists(symbol, timeframe):
            print("History present -> Checking for refresh...")
            data = pd.read_csv(
                f"{self.__base_dir}{timeframe}/{symbol}.csv", sep=",", dtype=float
            )
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
            print("Finished")
            return data
        else:  # Download full history
            print("No history -> Downloading full history...")
            data = self.__kucoin_fetcher.download_history(
                symbol, self.__absolute_start_date, timeframe, 16
            )
            data.to_csv(
                f"{self.__base_dir}{timeframe}/{symbol}.csv", sep=",", index=False
            )
            print("Finished")
            return data

    def __init_directories(self) -> None:
        """Private function that init all directories."""
        for tf in self.__kucoin_fetcher.timeframes:
            os.makedirs(f"{self.__base_dir}{tf}", exist_ok=True)
        os.makedirs(f"{self.__base_dir}list_available", exist_ok=True)
