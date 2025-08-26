FROM anasty17/mltb:latest

WORKDIR /usr/src/app

# Make sure /usr/src/app is writable
RUN chmod 777 /usr/src/app

# Create virtual environment
RUN python3 -m venv mltbenv

# Copy requirements and install dependencies
COPY requirements.txt .

RUN mltbenv/bin/pip install --no-cache-dir -r requirements.txt

# Copy rest of the source code
COPY . .

# Expose port 8080 for the Flask web server
EXPOSE 8080

# Run the start.sh script
CMD ["bash", "start.sh"]
