FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py encryption.py mock_firestore.py mock_encryption.py ./

ENV PORT=8080

CMD ["python", "main.py"] 