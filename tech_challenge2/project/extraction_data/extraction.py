from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
import os, re, uuid
import shutil
import time
import pandas as pd
from dotenv import load_dotenv

load_dotenv()
url = os.getenv("URL_PATH")
download_path = os.getenv("DOWNLOAD_PATH")
data_path = os.getenv("NEW_PATH")

print(url, download_path, data_path)

def download():
    options = Options()
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    drive = webdriver.Edge(options=options)
    drive.get(url)
    time.sleep(3)
    download_file = drive.find_element(by=By.CSS_SELECTOR, value='#divContainerIframeB3 > div > div.col-lg-9.col-12.order-2.order-lg-1 > form > div:nth-child(4) > div > div.row.mt-3 > div > div > div.list-avatar-row > div.content > p > a')
    download_file.click()

    time.sleep(10)

def get_files(path):
    file_csv = [f for f in os.listdir(path) if '.csv' in f.lower()]
    print(file_csv)
    files_result=[]
    for file in file_csv:
        aux = re.match("^IBOVDia_*", file)
        if aux != None:
            files_result.append(file)
    return files_result

def move_file():
    files_result = get_files(download_path)
    for file in files_result:
        new_path = data_path + file
        old_path = download_path + "/" + file
        shutil.move(old_path, new_path)

def save_file(df, partition:str):
    file_name = f'{uuid.uuid1()}.parquet'
    try:
        print('try create a dir')
        new_dir = f'{data_path}pq_files/{partition}'
        if not os.path.exists(new_dir):
            os.makedirs(new_dir)
            df.to_parquet(f'{new_dir}/{file_name}', engine='pyarrow')
    except Exception as e:
        print("except")
        return {"message_error": f"It was possible create a new dir\n{e}"}

def cleaning_file():
    files = get_files(data_path)    
    for file in files:
        df = pd.read_csv(f"{data_path}{file}", sep=";", encoding="utf-8")
        df = df.drop(df.columns[4], axis=1)
        renamer = {
            df.columns[0] : "Codigo",
            df.columns[1] : "Acao",
            df.columns[3] : "Part. (%)"
        }
        df = df.rename(mapper=renamer, axis=1)
        partition=f"{file[:4]}/{file[14:16]}/{file[11:13]}/{file[8:10]}"
        save_file(df, partition)
