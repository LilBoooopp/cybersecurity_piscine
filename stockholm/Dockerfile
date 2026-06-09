FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY stockholm.py .
COPY wannacry_extensions.txt .
COPY tests/ tests/
COPY Makefile .

RUN useradd -m testuser && mkdir -p /home/testuser/infection

USER testuser
ENV HOME=/home/testuser

CMD ["/bin/bash"]
