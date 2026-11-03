# PACT-lab runs entirely in this image: the reference implementations it stands on are fetched here at pinned
# commits and never run on the owner's machine itself.
#   MoLE drafts repo: EC-IHAT + EC-ACT Python PoC by the draft authors, with its pinned CFRG sigma-protocols submodule
#   CFRG VDAF draft repo: the Prio3 Python reference implementation
FROM python:3.13-slim
ARG MOLE_SHA=2789337242cd7d1b0e6853a967fba272b8a10748
ARG VDAF_SHA=e1d1e1c3854a34589c0c2d9b899a48533cac9004
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends git ca-certificates nodejs && rm -rf /var/lib/apt/lists/*
RUN set -eux; fetch() { git init -q "$1"; git -C "$1" remote add origin "$2"; git -C "$1" fetch -q --depth 1 origin "$3"; git -C "$1" checkout -q FETCH_HEAD; }; \
    fetch /deps/mole https://github.com/Moderation-of-unLinkable-Endorsements/internet-drafts "$MOLE_SHA"; \
    git -C /deps/mole submodule update -q --init --depth 1 poc/vendor/sigma-protocols; \
    fetch /deps/vdaf https://github.com/cfrg/draft-irtf-cfrg-vdaf "$VDAF_SHA"
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt && pip install --no-cache-dir --no-deps -e /deps/mole/poc -e /deps/vdaf/poc
RUN useradd --uid 10001 --create-home pact
WORKDIR /app
COPY .deployed* ./
COPY pactlab/ pactlab/
COPY tests/ tests/
USER pact
CMD ["python", "-m", "pytest", "-q", "-s"]
