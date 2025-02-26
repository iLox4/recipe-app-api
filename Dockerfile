# Use the official Python runtime image
FROM python:3.13

# Set the working directory inside the container
WORKDIR /app

# Set environment variables
# Prevents Python from writing pyc files to disk
ENV PYTHONDONTWRITEBYTECODE=1
# Prevents Python from buffering stdout and stderr
ENV PYTHONUNBUFFERED=1
# Set a default argument value
ARG DEV=false

# Upgrade pip
RUN pip install --upgrade pip

# Install system packages needed to compile psycopg2 from source
# - build-essential provides gcc, g++ and other compiling tools
# - libpq-dev are the PostgreSQL client development headers (needed by psycopg2)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    zlib1g-dev \
    libjpeg-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy the Django project  and install dependencies
COPY requirements.txt  /tmp/requirements.txt
COPY requirements.dev.txt /tmp/requirements.dev.txt

# Install dependecies
RUN pip install --no-cache-dir -r /tmp/requirements.txt
# If DEV is true when install dev dependencies as well
RUN if [ ${DEV} ]; \
        then pip install --no-cache-dir -r /tmp/requirements.dev.txt; \
    fi

# Delete tmp directory
RUN rm -rf /tmp

# Copy the Django project to the container
COPY ./app /app

# Add user to not use root user
RUN adduser --disabled-password --no-create-home django-user

# Creating directories for static files
RUN mkdir -p /vol/web/media && \
    mkdir -p /vol/web/static && \
    chown -R django-user:django-user /vol && \
    chmod -R 755 /vol

# Set user to newly created user
USER django-user

# Expose the Django port
EXPOSE 8000

# Run Django’s development server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
