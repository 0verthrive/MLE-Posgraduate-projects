from bs4 import BeautifulSoup
import requests
import pandas as pd
import json, os, glob

class Extraction:
    three_columns = [
        "exp_espumantes",
        "exp_suco",
        "exp_uva",
        "exp_vinho",
        "imp_espumantes",
        "imp_uvas_frescas",
        "imp_uvas_passas",
        "imp_suco",
        "imp_vinho"
    ]

    def __init__(self):
        self.url_default = "http://vitibrasil.cnpuv.embrapa.br/index.php?"

    def open_files(self, path): 
        base_dir = os.path.dirname(__file__)
        full_path = os.path.join(base_dir, path)
        with open(full_path, 'r', encoding='utf-8') as file:
            return json.load(file)

    def get_url(self, option, ano):
        options_url = self.open_files("urls.json")
        
        for keys, values in options_url.items():
            if isinstance(values, list):
                for item in values:
                    if option in item:
                        return "{}ano={}&{}".format(self.url_default, ano, item[option])
            elif keys == option:
                return "{}ano={}&{}".format(self.url_default, ano, values)

    def request_csv(self, option, ano, columns):
        matches = glob.glob(f"**/{option}.csv", recursive=True)
        if matches:
            df = pd.read_csv(matches[0], delimiter=";")
        else:
            return {'Message error': 'DF not found'}
            
        if option in self.three_columns:
            df.rename({ano: columns[1], ano+".1": columns[2]}, axis=1, inplace=True)
        else:
            df.rename({ano: columns[1]}, axis=1, inplace=True)
        return df.to_html(columns=columns)
    
    def request_site(self, option, ano):
        url = self.get_url(option, ano)
        response = requests.get(url)

        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            tables = soup.find_all('table', "tb_base tb_dados")

            if tables:
                for i, table in enumerate(tables):
                    rows = table.find_all('tr')
                    if rows:
                        headers = [th.text.strip() for th in rows[0].find_all('th')]
                        data = []
                        for row in rows[1:]:
                            cells = [td.text.strip() for td in row.find_all('td')]
                            data.append(cells)
                        if headers and data:
                            df = pd.DataFrame(data, columns=headers)
                        elif data:
                            df = pd.DataFrame(data)
                return df.to_html()