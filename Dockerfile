FROM python:3.12.1
COPY --from=ghcr.io/astral-sh/uv:0.5.18 /uv /uvx /bin/
COPY ./ /app

WORKDIR /app

CMD ["uv", "run", "main.py"]