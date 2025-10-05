import os
import re
import shutil
from dotenv import load_dotenv

load_dotenv()

download_path = os.getenv("DOWNLOAD_PATH")
data_path = os.getenv("CEPEA_PATH")

class Move:
    def __init__(self):
        pass

    def get_files(self, path):
        # pega todos os arquivos .xls que começam com "cepea-"
        file_xls = [f for f in os.listdir(path) if f.lower().endswith('.xls')]
        return [f for f in file_xls if re.match(r"^cepea-", f)]

    def move_file(self):
        files_result = self.get_files(download_path)

        # cria o diretório de destino se não existir
        os.makedirs(data_path, exist_ok=True)

        for file in files_result:
            old_path = os.path.join(download_path, file)
            new_path = os.path.join(data_path, file)

            # confere se o arquivo existe antes de mover
            if os.path.exists(old_path):
                shutil.move(old_path, new_path)
                print(f"✅ Moved file {file} to {new_path}")
            else:
                print(f"⚠️ Arquivo não encontrado: {old_path}")

    def run(self):
        self.move_file()


# if __name__ == "__main__":
#     move = Move()
#     move.run()
