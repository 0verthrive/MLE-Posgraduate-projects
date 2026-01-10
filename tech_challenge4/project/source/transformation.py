import pandas as pd
import uuid
from datetime import datetime
from dotenv import load_dotenv
import os
load_dotenv()

raw_path = os.getenv("RAW_DATA_PATH")
new_path = os.getenv("PROCESSED_DATA_PATH")

class Transformer:
    def __init__(self):
        pass

    def standardize_date(self, data, date_column):
        """
        Standardize the date format in the specified column to 'YYYY-MM-DD'.
        """
        if date_column not in data.columns:
            raise ValueError(f"Column '{date_column}' does not exist in the DataFrame.")
        
        data[date_column] = pd.to_datetime(data[date_column], utc=True).dt.strftime('%Y-%m-%d')
        return data
    
    def startadize_values(self, data, columns):
        """
        Standardize values in the specified column (example implementation).
        """
        if "Dividends" in columns:
            columns = [column for column in columns if column != "Dividends"]
        data[columns] = data[columns].round(2)

        return data

    def clean_data(self, data):
        """
        Clean the extracted data by handling missing values and duplicates.
        """
        if data is None:
            raise ValueError("Input data is None. Cannot clean data.")
        
        data = data.drop_duplicates() 
        
        return data
    
    def get_data(self):
        """
        Load data from the raw data path.
        """
        try:
            # Using a generator for speed
            files = [os.path.join(raw_path, f.name) for f in os.scandir(raw_path) if f.name.endswith('.csv')]
            data= pd.concat((pd.read_csv(f) for f in files), ignore_index=True)
            return data
        except FileNotFoundError:
            raise FileNotFoundError(f"File not found at path: {raw_path}")
    
    def save_data(self, data):
        """
        Save the transformed data to the specified path.
        """
        if data is None:
            raise ValueError("Input data is None. Cannot save data.")
        date=datetime.now()
        file_path = f"{new_path}/{date.year}/{date.month}/{date.day}/{uuid.uuid4()}.csv"
        data.to_csv(file_path, index=False)
        print(f"Data saved to {new_path}")

    def normalize_data(self):
        data = self.get_data()
        data = self.clean_data(data)
        data = self.standardize_date(data, 'Date')
        data = self.startadize_values(data, ['Open', 'High', 'Low', 'Close'])
        persist = self.save_data(data)
        
        return persist