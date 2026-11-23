FROM python:3.12-slim
WORKDIR /srv

# EXTRAS picks optional dependency groups from pyproject.toml: "" (API only), "dev", or "ml".
ARG EXTRAS=""

# The ML image installs the CPU-only torch first, in its own cached layer. The default Linux wheel
# bundles CUDA libraries (gigabytes) that a CPU server never uses.
RUN if echo "$EXTRAS" | grep -q ml; then \
      pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu; \
    fi

# The code must be here before `pip install .`: pyproject.toml lists the app packages by name.
COPY . .
RUN pip install --no-cache-dir ".${EXTRAS:+[$EXTRAS]}"

# Apply database migrations, then start the API.
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
