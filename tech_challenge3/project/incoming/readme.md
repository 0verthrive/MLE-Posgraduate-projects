# 📊 APIs de Ingestão de Dados – Preço do Café  

## 🚀 Objetivo  
Este projeto tem como finalidade **ingerir e consolidar dados relevantes para a análise do preço do café**.  
Serão consideradas duas fontes principais:  

1. **Dados históricos de preços da safra** (CEPEA).  
2. **Dados de clima** (temperatura, chuva, vento, etc.) obtidos de API pública.  

O objetivo final é **fornecer insumos para modelos de previsão de custos do café para a semana seguinte**.  

---

## 🗂️ Estrutura das APIs  

### `weather.py` ☁️  
- **Fonte**: [Open-Meteo Historical Weather API](https://open-meteo.com/en/docs/historical-weather-api) (uso gratuito para fins não comerciais).  
- **Função**:  
  - Requisita dados climáticos.  
  - Transforma a resposta em **DataFrame**.  
  - Prepara os dados para integração com informações de safra.  
- **Parâmetros de exemplo**:  
```json
{
  "start_date": "2024-01-01",
  "end_date": "2024-01-31",
  "daily": [
    "temperature_2m_max",
    "temperature_2m_min",
    "wind_speed_10m_max",
    "rain_sum",
    "precipitation_hours"
  ],
  "hourly": ["rain"]
}
```

### `cepea.py` ☕  

- **Fonte**: [CEPEA – Consultas ao Banco de Dados](https://www.cepea.org.br/br/consultas-ao-banco-de-dados-do-site.aspx)  
- **Função**:  
  - Utiliza **Selenium** para navegar na página.  
  - Seleciona as opções do **café robusta**. 
  - Faz download dos dados em **.xls**.  

- **Exemplo de saída estruturada**:  
```json
{
  "2025-09-26": {
    "valor_reais": "2.124,03",
    "variacao_dia": "0,10%",
    "variacao_mes": "-8,57%",
    "valor_dolar": "397,76"
  }
}
```

---

### `move.py` 
- **Função**:
  - Move os arquivos **.xls** da pasta download para a pasta em source **raw_file/cepea**

---

### `convert.py` 🔄  

- **Função**:  
  - Converte arquivos **.xls** para **.csv**.  
  - Implementado com **xlrd** e **csv**  

---

### `data_ingestion.py` 📥  

- **Função**:  
  - Orquestra o processo de ingestão.  
  - Chama as demais APIs (`weather`, `cepea`, `convert`).  
  - Unifica os dados em um único **DataFrame final**, pronto para consumo do modelo preditivo.  

---

## ⚙️ Fluxo de Ingestão  

```mermaid
    A[weather.py - dados climáticos] --> D[data_ingestion.py]
    B[cepea.py - dados de safra] --> C[convert.py - XLS → CSV] --> D[data_ingestion.py]
    D --> E[DataFrame unificado]
    E --> F[Modelo de previsão de preço do café]
```

