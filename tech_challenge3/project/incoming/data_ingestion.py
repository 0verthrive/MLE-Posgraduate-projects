## Essa API consome os dados gerados em uma semana 
class Ingestion(object):
    def __init__(self, data):
        self.data = data

    def ingest(self):
        print(self.data)