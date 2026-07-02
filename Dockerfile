ARG PYTHON_VERSION=3.11-slim
ARG CMAKE_BUILD_TYPE=Release
ARG CPP_EXECUTABLE_NAME=uav_pipeline

FROM python:${PYTHON_VERSION} AS builder

ARG CMAKE_BUILD_TYPE=Release
ARG CPP_EXECUTABLE_NAME=uav_pipeline

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    && rm -rf /var/lib/apt/lists/*

COPY pipeline/env_generator/requirements.txt ./pipeline/env_generator/requirements.txt

RUN pip install \
    --no-cache-dir \
    --no-compile \
    --target=/opt/python \
    -r pipeline/env_generator/requirements.txt

COPY pipeline/cpp_engine ./pipeline/cpp_engine

RUN cmake -S pipeline/cpp_engine -B pipeline/cpp_engine/build -DCMAKE_BUILD_TYPE=${CMAKE_BUILD_TYPE} \
    && cmake --build pipeline/cpp_engine/build --config ${CMAKE_BUILD_TYPE} -j \
    && cp pipeline/cpp_engine/build/${CPP_EXECUTABLE_NAME} /usr/local/bin/${CPP_EXECUTABLE_NAME} \
    && strip /usr/local/bin/${CPP_EXECUTABLE_NAME} || true

FROM python:${PYTHON_VERSION} AS runtime

ARG CPP_EXECUTABLE_NAME=uav_pipeline

ENV CPP_EXECUTABLE_NAME=${CPP_EXECUTABLE_NAME}
ENV PYTHONPATH=/opt/python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV MPLBACKEND=Agg

WORKDIR /app

COPY --from=builder /opt/python /opt/python
COPY --from=builder /usr/local/bin/${CPP_EXECUTABLE_NAME} /usr/local/bin/${CPP_EXECUTABLE_NAME}

COPY pipeline/env_generator ./pipeline/env_generator
COPY pipeline/path_planner ./pipeline/path_planner
COPY pipeline/scripts ./pipeline/scripts

RUN mkdir -p data/csv data/outputs data/plots \
    && chmod +x pipeline/scripts/run_all.sh \
    && rm -rf \
        /opt/python/pip \
        /opt/python/pip-* \
        /opt/python/setuptools \
        /opt/python/setuptools-* \
        /opt/python/pkg_resources \
    && find /opt/python -type d -name "__pycache__" -prune -exec rm -rf {} + \
    && find /opt/python -type d -name "tests" -prune -exec rm -rf {} + \
    && find /opt/python -type d -name "test" -prune -exec rm -rf {} + \
    && find /opt/python -type f -name "*.pyc" -delete \
    && find /opt/python -type f -name "*.pyo" -delete \
    && rm -rf /tmp/* /var/tmp/*

CMD ["sh", "pipeline/scripts/run_all.sh"]
