FROM python:3.11-slim

ARG UID=1000
ARG GID=1000
ARG USER=dev
ARG HOME=/home/dev
ARG APP=/app

RUN apt-get update && apt-get install -y --no-install-recommends \
      bash ca-certificates \
      git curl \
      adduser \
      libglib2.0-0 \
        libcairo2 \
        libpango-1.0-0 \
        libpangocairo-1.0-0 \
        libpangoft2-1.0-0 \
        libgdk-pixbuf-2.0-0 \
    && rm -rf /var/lib/apt/lists/* \
    && addgroup --gid "${GID}" "${USER}" \
    && adduser  --disabled-password --gecos "" \
                --uid "${UID}" --gid "${GID}" \
                --home "${HOME}" \
                "${USER}"

WORKDIR ${APP}

COPY docs/requirements.txt ${APP}/requirements.txt
COPY mkdocs.yml ${APP}/mkdocs.yml
COPY pdf_event_hook.py ${APP}/pdf_event_hook.py

RUN python -m venv ${APP}/.venv \
    && ${APP}/.venv/bin/pip install --upgrade pip wheel setuptools \
    && ${APP}/.venv/bin/pip install -r ${APP}/requirements.txt

ENV VIRTUAL_ENV=${APP}/.venv
ENV PATH="${VIRTUAL_ENV}/bin:${PATH}"

RUN chown -R "${UID}:${GID}" "${APP}" "${HOME}"

USER ${USER}
CMD ["bash"]
