FROM public.ecr.aws/lambda/python:3.12
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py ${LAMBDA_TASK_ROOT}/app.py
COPY src_shared ${LAMBDA_TASK_ROOT}/src_shared
CMD ["app.handler"]
