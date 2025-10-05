import os, re
from cepea import Cepea
from weather import Weather
from convert import Convert
from move import Move
import pandas as pd
from dotenv import load_dotenv
load_dotenv()

cepea_path = os.getenv("CEPEA_PATH")
weather_path = os.getenv("WEATHER_PATH")
data_path = os.getenv("TRAINING_DATA_PATH")

class Ingestion(object):
    def __init__(self):
        pass

    def get_files(self, path):
        return [f for f in os.listdir(path) if '.csv' in f.lower()]


    def aggregate(self):
        # Lê os dados dos arquivos CSV
        cepea = pd.read_csv(f"{cepea_path}/{self.get_files(cepea_path)[0]}")
        weather = pd.read_csv(f"{weather_path}/{self.get_files(weather_path)[0]}")

        # Realiza o merge dos dados
        merged_data = pd.merge(cepea, weather, on='date', how='inner')

        # Salva o resultado em um novo arquivo CSV
        merged_data.to_csv(f"{data_path}/", index=False)

        return "Data aggregated!"

    def ingest(self):
        print("Ingesting data...")
        cepea = Cepea("2015-01-01", "2025-09-30")
        weather = Weather("2015-01-01", "2025-09-30")
        move = Move()
        convert = Convert()
        
        cepea.run()
        weather.run()
        move.run()
        convert.run()
        
        self.aggregate()
        print("Data ingested!")
        return "Data ingested!"