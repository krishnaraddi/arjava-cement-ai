FROM python:3.9-slim
WORKDIR /app
COPY . /app
#COPY .env /app/.env
RUN pip install flask gym numpy
CMD ["python", "main.py"]
