# From ubuntu lts
FROM ubuntu:20.04

# Install dependencies
RUN apt-get update && apt-get install -y \
python3 \
python3-pip \
vim

# Install Required Python Packages
RUN pip3 install geopy folium Flask watchdog

# Copy only files in src directory to /app do not copy the src directory itself
COPY src/ /app

# Set the working directory
WORKDIR /app

# Run mesh-monitor.py on startup
CMD ["python3", "-m", "flask", "run", "--host=0.0.0.0"]