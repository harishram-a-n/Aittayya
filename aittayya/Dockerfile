# Dockerfile

# 1. Use an official lightweight Python image as a base
FROM python:3.11-slim

# 2. Set environment variables for production
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 3. Set the working directory inside the container
WORKDIR /app

# 4. Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy the rest of your application code
COPY . .

# 6. Expose the port the app will run on
EXPOSE 8080

# 7. Run the application using Gunicorn, a production-ready web server
# It will run the 'app' object from your 'app.py' file.
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "--threads", "4", "app:app"]