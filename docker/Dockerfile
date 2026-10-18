# The compiler comes from the published image; the result is one binary with the program and the
# lexicons inside it, on a runtime image that has no shell, no package manager and no Python.
ARG TELVAX_IMAGE=ghcr.io/telvax/telvax:latest
FROM ${TELVAX_IMAGE} AS builder

WORKDIR /app

COPY src ./src

RUN mkdir -p /out && telvax build --serve src/main.tvx -o /out/service

FROM gcr.io/distroless/cc-debian12:nonroot

COPY --from=builder /out/service /service

ENV PORT=8000 \
    TELVAX_METRICS=1 \
    TELVAX_LOG_FORMAT=json \
    TELVAX_CORS=* \
    TELVAX_RATE_LIMIT=100/min \
    TELVAX_SECURITY_HEADERS=1

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=4s --start-period=10s CMD ["/service", "--healthcheck", "/health"]

USER nonroot

ENTRYPOINT ["/service"]
