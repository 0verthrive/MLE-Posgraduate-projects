# 📊 Pipeline de Dados B3 com AWS

Este projeto constrói uma pipeline completa para **extrair, processar e analisar dados do pregão da B3**, utilizando os serviços **AWS S3, Glue, Lambda e Athena**.

---

## 🚀 Objetivo

Automatizar o processamento de dados do pregão da B3, organizando os dados em camadas (`raw` e `refined`) e possibilitando consultas analíticas via Athena.

---

## 🧱 Arquitetura

![Arquitetura do Projeto](image.png)

---

## ☁️ Serviços AWS Utilizados

### **S3**
Armazena os dados em diferentes estágios da pipeline:

- **Raw**: dados crus no formato Parquet  
   Estrutura: s3://<bucket-name>/raw/IBOV/yyyy/mm/dd/file.parquet


- **Refined**: dados tratados no formato Parquet, com partição por data  
   Estrutura: s3://<bucket-name>/refined/data=yyyy-mm-dd/file.parquet


- **Glue**: scripts de transformação e arquivos temporários

- **Athena results**: local onde o Athena salva os resultados de consultas

---

### **Lambda**
Monitora o bucket `raw/`. Sempre que um novo arquivo é adicionado, aciona o Glue Job automaticamente.

---

### **Glue**
Responsável por:

- Renomear colunas  
- Remover campos desnecessários  
- Adicionar e particionar por coluna `data`  
- Salvar os dados refinados no bucket `refined/`

---

### **AWS Glue Data Catalog**
Define a estrutura do banco de dados e tabela que permite a leitura dos dados refinados via Athena.

---

## 🛠️ Infraestrutura como Código (CDK)

O provisionamento da infraestrutura é feito com [AWS CDK (Cloud Development Kit)](https://docs.aws.amazon.com/cdk/v2/guide/home.html), utilizando Python.

### Estrutura do Projeto

cdk/  
├── cdk_stack.py # Stack principal que orquestra todos os recursos  
├── s3_stack.py # Stack do bucket S3  
├── lambda_stack.py # Stack da função Lambda  
├── glue_stacks.py # Stacks para Glue Database, Table e Job  
├── source/ # Scripts para Lambda e Glue  
└── config/ # Arquivos YAML de configuração  


---

## 📋 Pré-requisitos

- Python 3.8+
- [Node.js](https://nodejs.org/) (recomendado: LTS)
- [AWS CLI](https://aws.amazon.com/cli/) configurado
- [AWS CDK Toolkit](https://docs.aws.amazon.com/cdk/v2/guide/cli.html) instalado:
  ```bash
  npm install -g aws-cdk


⚙️ Instalação e Deploy
1. Clone o repositório e instale as dependências:
```bash
cd cdk
python -m venv .venv

# Linux/Mac
source .venv/bin/activate

# Windows
.venv\Scripts\activate.bat

pip install -r requirements.txt
```

2. Configure o arquivo:  
config/config.yaml

3. Crie e configure:  
config/environments.yaml

4. Gere o template CloudFormation:
```bash
cdk synth
```

5. Faça o deploy da infraestrutura:
```bash
cdk deploy
```
6. (Opcional) Remova os recursos:
```bash
cdk destroy
```

---
⚠️ Permissões
Certifique-se de que o usuário ou role da AWS utilizada possui permissões para criar e gerenciar os seguintes recursos:

- S3

- Glue

- Lambda

- IAM

- Athena

---

## 📌 Como Usar a Pipeline

Após o deploy da infraestrutura com CDK, a pipeline funcionará de forma **automatizada** com base no seguinte fluxo:

1. **Adicione um novo arquivo Parquet no bucket S3**, na pasta `raw/IBOV/yy/mm/dd/`.
2. A **função Lambda** será acionada automaticamente assim que o arquivo for detectado.
3. A Lambda dispara a execução do **Glue Job**, que:
   - Realiza as transformações nos dados.
   - Adiciona a coluna `data` (caso ainda não exista).
   - Salva os dados tratados no diretório `refined/`, particionado por data.
4. O **Glue Catalog** é atualizado (caso necessário), e os dados já podem ser consultados via **Athena**.

---

## 🧪 Exemplo de Execução

### 1. Upload do Arquivo para o Raw

Adicione um arquivo Parquet no seguinte caminho no S3:
   s3://<bucket-name>/refined/data=2025-08-06/dados_b3.parquet

### 4. Consulta no Athena

Você pode executar uma consulta no Athena como:

```sql
SELECT *
FROM b3_catalog_db.refined_ibov
WHERE data = DATE '2025-08-06'
ORDER BY qtde_teorica DESC;

```

