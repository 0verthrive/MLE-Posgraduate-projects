from selenium import webdriver
from selenium.webdriver.common.by import By
import os, time



class Cepea():
    def __init__(self, start_date, end_date):
        self.url = "https://www.cepea.esalq.usp.br/br/indicador/soja.aspx"
        dirname = os.path.dirname(__file__)
        self.dir_dowload = os.path.join(dirname, f"source/training_data/raw_files/cepea/")
        self.start_date = start_date
        self.end_date = end_date

    def inicialize_driver(self):
        driver = webdriver.Edge()
        return driver
    
    def selecionar_data(self, driver, campo_xpath: str, ano: str, mes: str, dia: str):
        
        # clicar no campo para abrir o calendário
        campo = driver.find_element(By.XPATH, campo_xpath)
        campo.click()
        time.sleep(1)

        # pegar o id do campo (ex: "periodo-de") e construir o root
        campo_id = campo.get_attribute("id")  # ex: "periodo-de"
        root_id = f"{campo_id}_root"

        # selecionar ano
        anos = driver.find_elements(By.XPATH, f'//*[@id="{root_id}"]/div/div/div/div/div[1]/select[1]/option')
        for a in anos:
            if a.text.strip() == ano:
                a.click()
                break

        time.sleep(5)

        # selecionar mês
        meses = driver.find_elements(By.XPATH, f'//*[@id="{root_id}"]/div/div/div/div/div[1]/select[2]/option')
        for m in meses:
            if m.text.strip().lower() == mes.lower():
                m.click()
                break

        time.sleep(5)

        # selecionar dia válido
        dias = driver.find_elements(
            By.XPATH,
            f'//*[@id="{root_id}"]//div[contains(@class,"picker__day") and not(contains(@class,"picker__day--disabled"))]'
        )
        time.sleep(2)
        for d in dias:
            if d.text.strip() == dia:
                d.click()
                break
        time.sleep(5)

    def get_cepea_data(self, driver):
        driver.get(self.url)
        
        produto = driver.find_element(By.XPATH, '//*[@id="frm-selecionar"]/div[1]/div/div[2]/div/div[2]/div/label[7]')
        produto.click()
        time.sleep(2)

        produto_tipo = driver.find_element(By.XPATH, '//*[@id="frm-selecionar"]/div[1]/div/div[3]/div/div[2]/div/label[2]')
        produto_tipo.click()
        time.sleep(5)

        # selecionar data inicial: 01/01/2024
        self.selecionar_data(driver, '//*[@id="periodo-de"]', self.start_date[2], self.start_date[1], self.start_date[0])

        # selecionar data final: 07/01/2024
        self.selecionar_data(driver, '//*[@id="periodo-ate"]', self.end_date[2], self.end_date[1], self.end_date[0])
        time.sleep(5)

        gerar_excel= driver.find_element(By.XPATH, '//*[@id="adicionar"]')
        gerar_excel.click()

        time.sleep(10) 

        download = driver.find_element(By.XPATH, '//*[@id="false"]/td[5]/a[2]')
        download.click()

        time.sleep(10)  # esperar o download completar

        driver.quit()