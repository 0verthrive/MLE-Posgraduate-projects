# Deploy no ambiente específico — AWS Account + us-east-1 (N. Virginia)

## O que você precisa alterar

### 1. Conta AWS
No arquivo `cdk.json`, troque:
```json
"account": "111111111111"
```
Pelo **ID real da sua conta AWS**.

### 2. Região
No mesmo arquivo, mantenha:
```json
"region": "us-east-1"
```
Essa é a região **N. Virginia**.

### 3. Nome do projeto e stage
Ajuste conforme quiser isolar seus recursos:
```json
"project_name": "passos-magicos",
"stage": "dev"
```
Sugestão:
- `stage=dev` para datathon/teste
- `stage=hml` para homologação
- `stage=prod` para produção

## Exemplo final de `cdk.json`
```json
{
  "app": "python app.py",
  "context": {
    "project_name": "passos-magicos",
    "stage": "dev",
    "account": "123456789012",
    "region": "us-east-1"
  }
}
```

## Pré-requisitos
- AWS CLI configurado
- credenciais com permissão para:
  - CloudFormation
  - IAM
  - S3
  - Lambda
  - ECR
  - ECS
  - Glue
  - Step Functions
  - DynamoDB
  - CloudWatch
- Node.js instalado
- Python 3.11+ instalado

## Comandos para rodar

### Linux / Mac
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
npm install -g aws-cdk
aws sts get-caller-identity
cdk bootstrap aws://123456789012/us-east-1
cdk synth
cdk deploy --all --require-approval never
```

### Windows PowerShell
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
npm install -g aws-cdk
aws sts get-caller-identity
cdk bootstrap aws://123456789012/us-east-1
cdk synth
cdk deploy --all --require-approval never
```

## Deploy sem alterar `cdk.json`
Você também pode sobrescrever tudo por linha de comando:
```bash
cdk deploy --all \
  -c project_name=passos-magicos \
  -c stage=dev \
  -c account=123456789012 \
  -c region=us-east-1 \
  --require-approval never
```

## Saídas esperadas após o deploy
Você deve copiar do output do CDK:
- nome do bucket principal
- nome da tabela DynamoDB
- ARN da Step Function
- URL da API

## Custos e pontos de atenção
- o projeto cria **VPC com NAT Gateway**, que pode gerar custo mesmo sem uso intenso
- Glue e ECS também geram custo por execução
- para demo, use `stage=dev` e destrua o ambiente quando terminar

## Para remover o ambiente
```bash
cdk destroy --all
```

## Ajustes opcionais antes de produção
- trocar `Function URL` por `API Gateway`
- mover imagens para repositórios ECR explícitos
- revisar políticas IAM com menor privilégio
- usar `RemovalPolicy.RETAIN` em dados críticos
