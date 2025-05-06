FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies required for TA-Lib
RUN apt-get update && apt-get install -y \
    build-essential \
    wget \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install TA-Lib
RUN wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz && \
    tar -xvzf ta-lib-0.4.0-src.tar.gz && \
    cd ta-lib/ && \
    ./configure --prefix=/usr && \
    make && \
    make install && \
    cd .. && \
    rm -rf ta-lib-0.4.0-src.tar.gz ta-lib/

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install TA-Lib Python wrapper
RUN pip install --no-cache-dir ta-lib

# Additional dependencies that might not be in requirements.txt
RUN pip install --no-cache-dir pandas-ta plotly yfinance

# Copy the entire project
COPY . .

# Set the entrypoint to run the backtester
ENTRYPOINT ["python", "-m", "mtfema_backtester.main"]

# Default command (can be overridden)
CMD ["--help"] 