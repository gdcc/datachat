# Use an official Python runtime as a parent image
FROM python:3.11-slim

RUN apt update;apt install -y git vim curl wget

# Set the working directory in the container
WORKDIR /app

# Copy only the requirements file first to leverage Docker cache
COPY requirements.txt /app/

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . /app

# Make port 8501 available to the world outside this container
EXPOSE 8501

# Set environment variable to ensure Python can find the app module
ENV PYTHONPATH=/app

# Run app.py when the container launches
CMD ["streamlit", "run", "app/app.py"]

