FROM python:3.11-buster as builder

RUN pip install uv

WORKDIR /app

COPY pyproject.toml ./
RUN touch README.md

RUN uv pip install --system .

FROM python:3.11-slim-buster as runtime

COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY scraper ./scraper

ENTRYPOINT ["python", "-m", "scraper.main:server"]