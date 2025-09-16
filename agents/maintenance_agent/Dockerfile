FROM python:3.9-slim
WORKDIR /app
COPY . /app
#COPY .env /app/.env
RUN pip install -r requirements.txt
ENV PROJECT_ID=my-project
CMD ["python", "main.py"]
