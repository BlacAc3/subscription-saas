FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY ./app /app/

# Set environment variables
ENV PORT=8000
ENV MONGO_URI=mongodb://localhost:27017
ENV SECRET_KEY=your-secret-key-here

# Expose the application port
EXPOSE $PORT

# Create a non-root user and switch to it
RUN adduser --disabled-password --gecos '' appuser
USER appuser

# Run the application
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port $PORT"]
