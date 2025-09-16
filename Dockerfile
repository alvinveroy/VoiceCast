# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Create a non-root user
RUN useradd --create-home appuser

# Copy the requirements file into the container
COPY --chown=appuser:appuser requirements.txt .

# Install build dependencies
RUN apt-get update && apt-get install -y gcc python3-dev && rm -rf /var/lib/apt/lists/*

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application's code into the container
COPY --chown=appuser:appuser src/ ./src
COPY --chown=appuser:appuser main.py .

# Switch to the non-root user
USER appuser



# Run main.py when the container launches
CMD ["python", "main.py", "start"]
