""" Essa API consome os dados no range de uma semana no CEPEA """

# Imports
import requests
import json
import selenium


class Ingestion(object):
    def __init__(self, data):
        self.data = data

    def get_data(self):
        return self.data
    
    def set_data(self, data):
        self.data = data

    def save_data(self, filepath):
        with open(filepath, 'w') as file:
            file.write(self.data)

    def ingest(self):
        print(self.data)