FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml README.md py.typed ./
COPY src/ src/

RUN pip install --no-cache-dir . textual-serve

COPY demo/ demo/

ENV PORT=8000
EXPOSE 8000

CMD ["python", "demo/serve.py"]
