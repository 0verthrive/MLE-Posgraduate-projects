import os
import csv
import re
import pandas as pd
import xlrd
from dotenv import load_dotenv

load_dotenv()

file_path = os.getenv("CEPEA_PATH")

class Convert:
    def __init__(self):
        pass

    def get_files(self, path):
        """Lista arquivos .xls no diretório."""
        return [f for f in os.listdir(path) if f.lower().endswith('.xls')]

    def csv_from_excel(self, file_path):
        """Converte o primeiro arquivo XLS para CSV com tratamento de erro."""
        files = self.get_files(file_path)
        if not files:
            print("Nenhum arquivo .xls encontrado.")
            return

        file = files[0]
        xls_full_path = os.path.join(file_path, file)
        csv_path = os.path.join(file_path, f"{os.path.splitext(file)[0]}.csv")

        print(f"📂 Processando: {xls_full_path}")

        try:
            # Tentativa padrão com xlrd (para .xls antigos)
            wb = xlrd.open_workbook(xls_full_path)
            sh = wb.sheet_by_index(0)
            print("✅ Arquivo aberto com xlrd")

            with open(csv_path, "w", newline="", encoding="utf-8") as csv_file:
                wr = csv.writer(csv_file, quoting=csv.QUOTE_ALL)
                for rownum in range(3, sh.nrows):  # pula as 3 primeiras linhas
                    wr.writerow(sh.row_values(rownum))

        except xlrd.compdoc.CompDocError as e:
            print(f"⚠️ Erro de corrupção detectado com xlrd: {e}")
            print("Tentando abrir com pandas + openpyxl...")

            try:
                df = pd.read_excel(xls_full_path, engine="openpyxl", header=None)
                df = df.iloc[3:]  # pula as 3 primeiras linhas
                df.to_csv(csv_path, index=False, header=False, quoting=csv.QUOTE_ALL, encoding="utf-8")
                print("✅ Arquivo convertido com pandas/openpyxl!")

            except Exception as e2:
                print(f"❌ Falha ao abrir com pandas: {e2}")

        except Exception as e:
            print(f"❌ Erro inesperado: {e}")

        else:
            print("✅ Conversão concluída com sucesso!")
        
        finally:
            print("🟢 Processo finalizado.\n")

    def run(self):
        self.csv_from_excel(file_path)


if __name__ == "__main__":
    Convert().run()
