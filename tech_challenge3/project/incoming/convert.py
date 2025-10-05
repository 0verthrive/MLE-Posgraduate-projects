import xlrd
import csv
from dotenv import load_dotenv
import os, re
load_dotenv()

file_path = os.getenv("CEPEA_PATH")

class Convert:
    def __init__(self):
        pass

    def get_files(self, path):
        return [f for f in os.listdir(path) if '.xls' in f.lower()]
        
    def csv_from_excel(self, file_path):
        file = self.get_files(file_path)
        print(f'file: {file}')

        wb = xlrd.open_workbook(f'{file_path}/{file[0]}')
        print('Workbook opened!')
        sh = wb.sheet_by_name('Plan 1')
        
        csv_file = open(f'{file_path}/{file[0].split(".")[0]}.csv', 'w', newline='', encoding='utf-8')
        wr = csv.writer(csv_file, quoting=csv.QUOTE_ALL)

        for rownum in range(3, sh.nrows):
            wr.writerow(sh.row_values(rownum))

        csv_file.close()
        print("File converted!")

    def run(self):
        self.csv_from_excel(file_path)

# if __name__ == "__main__":
#     convert = Convert()
#     convert.run()