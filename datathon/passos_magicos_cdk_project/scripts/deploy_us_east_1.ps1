param(
    [string]$AccountId = "123456789012",
    [string]$ProjectName = "passos-magicos",
    [string]$Stage = "dev"
)

$Region = "us-east-1"

python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
npm install -g aws-cdk
aws sts get-caller-identity
cdk bootstrap aws://$AccountId/$Region
cdk synth `
  -c project_name=$ProjectName `
  -c stage=$Stage `
  -c account=$AccountId `
  -c region=$Region
cdk deploy --all `
  -c project_name=$ProjectName `
  -c stage=$Stage `
  -c account=$AccountId `
  -c region=$Region `
  --require-approval never
