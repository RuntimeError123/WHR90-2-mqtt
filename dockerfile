FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
COPY WHR90.py.py .
RUN pip install --no-cache-dir -r requirements.txt
CMD ["python", "WHR90.py"]