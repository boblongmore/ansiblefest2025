# Use the official Python image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy project files
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port FastAPI will run on
EXPOSE 5000

# Start the FastAPI app with Uvicorn
CMD ["uvicorn", "exporter-app.exporter:app", "--host", "0.0.0.0", "--port", "5000"]
