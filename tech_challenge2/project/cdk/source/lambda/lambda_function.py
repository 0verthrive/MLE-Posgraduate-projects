import json, os
import boto3
import urllib.parse


glue = boto3.client('glue')

def handler(event, context):
    records = event.get('Records', [])
    job_name = os.environ['GLUE_JOB_NAME']

    # Extrai info do evento S3
    record = records[0]
    bucket = record['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(record['s3']['object']['key'])

    print(f"Arquivo recebido: s3://{bucket}/{key}")

    # Aciona o Glue Job com os argumentos
    response = glue.start_job_run(
        JobName=job_name,  
        Arguments={
            '--SOURCE_BUCKET': bucket,
            '--SOURCE_KEY': key,
            '--JOB_NAME': job_name  
        }
    )

    print(f"Glue Job iniciado com JobRunId: {response['JobRunId']}")

    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Glue acionado com sucesso',
            'JobRunId': response['JobRunId'],
            'file': f"s3://{bucket}/{key}"
        })
    }
