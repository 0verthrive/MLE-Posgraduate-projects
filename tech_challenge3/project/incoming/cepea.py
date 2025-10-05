from selenium import webdriver
from selenium.webdriver.common.by import By
import os, time



class Cepea():
    def __init__(self, start_date, end_date):
        self.url = "https://www.cepea.org.br/br/consultas-ao-banco-de-dados-do-site.aspx"
        self.start_date = start_date
        self.end_date = end_date

    
    def selecionar_data(self, driver, campo_xpath: str, ano: str, mes: str, dia: str):
        
        # clicar no campo para abrir o calendário
        campo = driver.find_element(By.XPATH, campo_xpath)
        campo.click()
        time.sleep(2)

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
        time.sleep(5)
        for d in dias:
            if d.text.strip() == dia:
                d.click()
                break
        time.sleep(5)

    def get_cepea_data(self):
        driver = webdriver.Edge()
        driver.get(self.url)
        time.sleep(5)
        
        produto = driver.find_element(By.XPATH, '//*[@id="frm-selecionar"]/div[1]/div/div[2]/div/div[2]/div/label[7]')
        produto.click()
        time.sleep(2)

        produto_tipo = driver.find_element(By.XPATH, '//*[@id="frm-selecionar"]/div[1]/div/div[3]/div/div[2]/div/label[2]')
        produto_tipo.click()
        time.sleep(5)

        # 🧠 Quebra e converte as datas
        meses_map = {
            "01": "janeiro", "02": "fevereiro", "03": "março", "04": "abril",
            "05": "maio", "06": "junho", "07": "julho", "08": "agosto",
            "09": "setembro", "10": "outubro", "11": "novembro", "12": "dezembro"
        }

        ano_i, mes_i, dia_i = self.start_date.split('-')
        ano_f, mes_f, dia_f = self.end_date.split('-')

        mes_i_nome = meses_map[mes_i]
        mes_f_nome = meses_map[mes_f]

        # 🗓️ Selecionar data inicial
        self.selecionar_data(driver, '//*[@id="periodo-de"]', ano_i, mes_i_nome, str(int(dia_i)))

        # 🗓️ Selecionar data final
        self.selecionar_data(driver, '//*[@id="periodo-ate"]', ano_f, mes_f_nome, str(int(dia_f)))
        
        time.sleep(5)

        gerar_excel = driver.find_element(By.XPATH, '//*[@id="adicionar"]')
        gerar_excel.click()
        time.sleep(10)

        download = driver.find_element(By.XPATH, '//*[@id="false"]/td[5]/a[2]')
        download.click()
        time.sleep(10)

        driver.quit()

    
    def run(self):
        self.get_cepea_data()
        print("✅ CEPEA data downloaded!")