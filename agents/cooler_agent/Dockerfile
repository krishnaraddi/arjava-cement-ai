# Use a lightweight Python base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install flask gym numpy  
# Copy source code
COPY main.py .

# Expose port 8080 for Cloud Run
EXPOSE 8080

# Start the Flask server
CMD ["python", "main.py"]