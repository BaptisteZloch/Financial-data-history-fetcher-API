from datetime import datetime
from typing import Callable
import pandas as pd
import os
import time
from random import randint
from kucoin.client import Market
from concurrent.futures import ThreadPoolExecutor, as_completed


class KucoinDataFetcher:
    __client = Market(url="https://api.kucoin.com")
    __timeframes_in_s: dict[str, int] = {
        "1min": 60,
        "2min": 120,
        "5min": 300,
        "15min": 900,
        "30min": 1800,
        "1hour": 3600,
        "2hour": 7200,
        "4hour": 14400,
        "12hour": 43200,
        "1day": 86400,
    }
    timeframes: tuple[str] = tuple(__timeframes_in_s.keys())

    def __construct_timestamp_list(
        self,
        start_timestamp: int,
        end_timestamp: int,
        timeframe: str,
        exchange_limit: int = 1500,
    ) -> list[int]:
        """Private function that generates a list of timestamps spaced of `exchange_limit` times `timeframe`.

        Args:
            start_timestamp (str): The initial timestamp.
            end_timestamp (str): The final timestamp.
            timeframe (str): The desired timeframe, sould be 1min, 2min, 5min, 15min, 1hour, 4hour, 1day...
            exchange_limit (int, optional): The exchange limit : 1500 for Kucoin here.. Defaults to 1500.

        Returns:
            list[int]: The list of timestamps.
        """
        remaining = (end_timestamp - start_timestamp) // self.__timeframes_in_s[
            timeframe
        ]

        timestamp_i = end_timestamp
        timestamps = [timestamp_i]

        while remaining > exchange_limit:
            timestamp_i = (
                timestamp_i - self.__timeframes_in_s[timeframe] * exchange_limit
            )
            remaining = remaining - exchange_limit
            timestamps.append(timestamp_i)

        timestamps.append(start_timestamp)

        return sorted(timestamps, reverse=True)

    @staticmethod
    def __handle_429_error(func: Callable) -> Callable:
        """Static private decorator that handle error 429 response from Kucoin API.

        Args:
            func (Callable): The function to wrap.

        Returns:
            Callable: The wrapper.
        """

        def wrapper(*args, **kwargs):
            passed = False
            while passed == False:
                try:
                    return func(*args, **kwargs)
                except:
                    time.sleep(randint(10, 100) / 100)
                    pass

        return wrapper

    @__handle_429_error
    def __get_data(
        self, symbol: str, start_at: int, end_at: int, timeframe: str = "15min"
    ) -> pd.DataFrame:
        """Private function that uses Kucoin API to get the data for a specific symbol and timeframe.

        Args:
            symbol (str): The symbol for the data we want to extract. Defaults to "BTC-USDT".
            start_at (int): The starting timestamp and. Note that this function could only outputs 1500 records. If the timeframe and the timestamps don't satisfy it, it will return a dataframe with 1500 records from the starting timestamp.
            end_at (int): The ending timestamp.
            timeframe (str, optional): The timeframe, it must be 1min, 2min, 5min, 15min, 1hour, 4hour, 1day... Defaults to '15min'.

        Returns:
            Optional[pd.DataFrame]: The dataframe containing historical records.
        """
        klines = self.__client.get_kline(
            f"{symbol}", timeframe, startAt=start_at, endAt=end_at
        )
        df = pd.DataFrame(
            klines,
            columns=[
                "Date",
                "Open",
                "High",
                "Low",
                "Close",
                "Volume",
                "Amount",
            ],
            dtype=float,
        )
        df["Date"] = df["Date"].astype(int)

        return df

    def get_symbols(self) -> list[str]:
        """Get a list of all symbols in kucoin

        Returns:
            list[str]: The symbol's list.
        """
        tickers = self.__client.get_all_tickers()
        if tickers is not None:
            return [tik["symbol"] for tik in tickers["ticker"]]
        raise ValueError("Error, no symbols found.")

    def download_history(
        self, symbol: str, since: str, timeframe: str, jobs: int = -1
    ) -> None:
        """Download a set of historical data and save it.

        Args:
            symbol (str): The symbol for the data we want to extract. Defaults to "BTC-USDT".
            since (str): The initial date in format : dd-mm-yyyy.
            timeframe (str): The timeframe, it must be 1min, 2min, 5min, 15min, 1hour, 4hour, 1day... Defaults to '15min'.
            jobs (int, optional): The number of thread to parallelize the code. Defaults to -1.

        Raises:
            ValueError: Error in using parallelism.
        """
        start_timestamp = int(datetime.strptime(since, "%d-%m-%Y").timestamp())
        end_timestamp = int(datetime.now().timestamp())

        assert (
            start_timestamp < end_timestamp
        ), "Error, the starting timestamp must be less than ending timestamp"

        timestamps = self.__construct_timestamp_list(
            start_timestamp, end_timestamp, timeframe
        )

        df = pd.DataFrame(
            columns=["Date", "Open", "High", "Low", "Close", "Volume", "Amount"],
            dtype=float,
        )

        if jobs == -1 or jobs == 1:
            for i in range(len(timestamps) - 1):
                df = pd.concat(
                    [
                        df,
                        self.__get_data(
                            symbol, timestamps[i + 1], timestamps[i], timeframe
                        ),
                    ]
                )

        elif jobs > 1 and jobs <= 50:
            with ThreadPoolExecutor(max_workers=jobs) as executor:
                processes = [
                    executor.submit(
                        self.__get_data,
                        symbol,
                        timestamps[i + 1],
                        timestamps[i],
                        timeframe,
                    )
                    for i in range(len(timestamps) - 1)
                ]

            for task in as_completed(processes):
                df = pd.concat([df, task.result()])
        else:
            raise ValueError(
                "Error, jobs must be between 50 and 2 to use parallelism or -1 and 1 to do it sequentially."
            )

        df = df.sort_values(by="Date")
        df["Timestamp"] = df["Date"].astype(int)
        df["Date"] = df["Date"].astype(int).apply(datetime.fromtimestamp)
        df = df.set_index("Date")

        if not os.path.exists(f"../../database/{timeframe}/"):
            os.makedirs(f"../../database/{timeframe}/")

        df.to_csv(f"../../database/{timeframe}/{symbol}.csv", sep=",", index=False)
