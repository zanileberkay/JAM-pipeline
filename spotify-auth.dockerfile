FROM python:3.9-slim

WORKDIR /app

# Copy your application code and the Firebase Admin SDK JSON file
COPY . /app
# Ensure the JSON file is located at the specified path in your source directory
COPY /home/ahmetberkayunal18/backend-api/key/db-key.json /app/key/db-key.json

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8080
ENV FLASK_ENV=production
CMD ["python", "server.py"]
