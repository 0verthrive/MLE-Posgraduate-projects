import yfinance as yf
from datetime import datetime
from dotenv import load_dotenv
import os
load_dotenv()
path_raw = os.getenv("PATH_RAW_DATA")


class DataExtractor:
    def __init__(self, symbol, period):
        
        self.symbol = symbol
        self.data = None
        self.period = period

    def fetch_data(self):
        """
        Fetch historical market data for the given symbol.
        """
        try:
            self.data = yf.Ticker(self.symbol).history(period=self.period)
        except Exception as e:
            raise RuntimeError(f"Failed to fetch data for {self.symbol}: {e}")
        
        return self.data

    def persist_data(self):
        """
        Return the fetched data.
        
        :return: DataFrame containing the historical market data.
        """
        if self.data is None:
            raise ValueError("Data is none. Fetch data before persisting.")
        
        self.data.to_csv(f"{path_raw}/{self.symbol}_{self.period}_{datetime.now().date}_data.csv")

        return f"Persisted data to {path_raw}/{self.symbol}_{self.period}_{datetime.now().date}_data.csv"
    
    def get_data(self):
        """
        Fetch data and persist it.
        :return: Message indicating where the data has been persisted.
        """
        self.fetch_data()
        persisted = self.persist_data()
        return persisted