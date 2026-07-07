FROM python:3.14-slim

RUN pip install --no-cache-dir uv==0.8.13

WORKDIR /code

COPY ./pyproject.toml ./README.md ./uv.lock* ./

COPY ./app ./app

RUN uv sync --frozen --no-dev

EXPOSE 8080

# No frontend build stage yet -- tech-spec §8's "single deployable: FastAPI +
# built SPA assets" isn't achievable until the React SPA is scoped; this
# image serves the API only.
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
