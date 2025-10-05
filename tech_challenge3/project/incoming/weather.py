import openmeteo_requests
import pandas as pd
import requests_cache
from retry_requests import retry
import os
from dotenv import load_dotenv
load_dotenv()


cache_session = requests_cache.CachedSession('.cache', expire_after = -1)
retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
openmeteo = openmeteo_requests.Client(session = retry_session)
file_path = os.getenv("WEATHER_PATH")

class Weather():
    def __init__(self, start_date, end_date):
        self.url = "https://archive-api.open-meteo.com/v1/archive"
        self.params = {
                "latitude": 52.52,
                "longitude": 13.41,
                "start_date": start_date,
                "end_date": end_date,
                "daily": ["temperature_2m_max", "temperature_2m_min", "wind_speed_10m_max", "rain_sum", "precipitation_hours"],
                "hourly": ["rain"],
                "timezone": "America/Sao_Paulo",
            }
        self.file_name = f"{start_date}_{end_date}_weather.csv"
        dirname = os.path.dirname(__file__)
        self.path_file = os.path.join(dirname, f'{file_path}/{self.file_name}')

    def get_weather(self):
        return openmeteo.weather_api(self.url, params=self.params)[0]

    def daily_data(self, daily):
        daily_data = {"date": pd.date_range(
            start = pd.to_datetime(daily.Time(), unit = "s", utc = True),
            end = pd.to_datetime(daily.TimeEnd(), unit = "s", utc = True),
            freq = pd.Timedelta(seconds = daily.Interval()),
            inclusive = "left"
        )}

        daily_data["temperature_2m_max"] = daily.Variables(0).ValuesAsNumpy()
        daily_data["temperature_2m_min"] = daily.Variables(1).ValuesAsNumpy()
        daily_data["wind_speed_10m_max"] = daily.Variables(2).ValuesAsNumpy()
        daily_data["rain_sum"] = daily.Variables(3).ValuesAsNumpy()
        daily_data["precipitation_hours"] = daily.Variables(4).ValuesAsNumpy()
        
        return pd.DataFrame(data = daily_data)
    
    def hourly_data(self, hourly):

        hourly_data = {"date": pd.date_range(
            start = pd.to_datetime(hourly.Time(), unit = "s", utc = True),
            end = pd.to_datetime(hourly.TimeEnd(), unit = "s", utc = True),
            freq = pd.Timedelta(seconds = hourly.Interval()),
            inclusive = "left"
        )}

        hourly_data["rain"] = hourly.Variables(0).ValuesAsNumpy()
        return pd.DataFrame(data = hourly_data)

    def aggregate_data(self, hourly_dataframe, daily_dataframe):
        return pd.merge_asof(daily_dataframe, hourly_dataframe, on="date", direction="backward", tolerance=pd.Timedelta("1D")).fillna(0)
    
    def save_file(self, dataframe, filepath):
        dataframe.to_csv(filepath, index = False)

    def run(self):
        response = self.get_weather()
        daily_dataframe = self.daily_data(response.Daily())
        hourly_dataframe = self.hourly_data(response.Hourly())
        dataframe = self.aggregate_data(hourly_dataframe, daily_dataframe)
        self.save_file(dataframe, self.path_file)
        return f"Dataframe de clima {self.file_name} salvo com sucesso!"
    
# # teste
# if __name__ == "__main__":
#     weather = Weather("2024-01-01", "2024-01-07")
#     weather.run()