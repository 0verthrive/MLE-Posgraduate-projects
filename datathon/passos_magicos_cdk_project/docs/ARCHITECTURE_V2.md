# Arquitetura V2 — Passos Mágicos

## Visão executiva
A solução foi organizada como uma plataforma **MLOps em AWS** para prever o risco de defasagem escolar, com foco em rastreabilidade, baixo acoplamento e deploy reproduzível via CDK.

## Fluxo ponta a ponta
```mermaid
flowchart TD
    A[Dados educacionais 2022-2024] --> B[S3 Bronze]
    B --> C[Glue ETL]
    C --> D[S3 Silver]
    D --> E[Glue Data Quality]
    E --> F[S3 Gold]
    F --> G[Step Functions]
    G --> H[ECS Fargate Training]
    H --> I[S3 Artifacts - modelo joblib]
    I --> J[FastAPI em Lambda Container]
    J --> K[/predict]
    J --> L[S3 Predictions]
    J --> M[DynamoDB Metadata]
    G --> N[Lambda Monitoring]
    N --> O[CloudWatch Dashboard]
    F --> P[Athena]
```

## Componentes

### 1. Camadas do Data Lake
- **Bronze**: dados brutos recebidos pela ingestão.
- **Silver**: dados padronizados, tratados e enriquecidos.
- **Gold**: dados analíticos e features finais para consumo do modelo.
- **Artifacts**: modelos treinados, scripts e arquivos auxiliares.
- **Predictions**: histórico das inferências geradas pela API.
- **Monitoring**: saídas e snapshots usados no acompanhamento de drift.

### 2. Ingestão
- **SQS** desacopla a entrada de eventos.
- **Lambda container** recebe a mensagem, grava o arquivo bruto no S3 e registra metadados no DynamoDB.

### 3. Processamento
- **Glue ETL** transforma dados da Bronze para Silver/Gold.
- **Glue Data Quality** executa checagens mínimas antes do treinamento.

### 4. Orquestração
- **Step Functions** coordena ETL → Data Quality → Training → Monitoring.

### 5. Treinamento
- **ECS Fargate** executa o job de treinamento em container.
- O modelo final é salvo em **S3/artifacts/models**.

### 6. Serving
- **FastAPI em Lambda container** expõe o endpoint `/predict`.
- A API lê o modelo mais recente do S3, registra predições e pode disparar nova execução da pipeline.

### 7. Observabilidade
- **CloudWatch Logs**: execução técnica.
- **CloudWatch Dashboard**: indicadores de volume e drift.
- **DynamoDB**: status e metadados de execução.

## Decisões arquiteturais
- **CDK em Python** para facilitar manutenção e reuso do projeto.
- **Lambda container para API** por simplicidade operacional e custo reduzido.
- **Fargate para treinamento** por ser mais flexível que Lambda para workloads de ML.
- **S3 + Athena** como lakehouse analítico com baixo custo.

## Melhorias recomendadas para produção
- adicionar **VPC endpoints** para reduzir tráfego via NAT
- proteger a API com **API Gateway + authorizer**
- usar **ECR repositórios dedicados** e pipeline CI/CD
- evoluir monitoramento com baseline estatístico e alertas automáticos
- parametrizar sizing por ambiente (`dev`, `hml`, `prod`)
