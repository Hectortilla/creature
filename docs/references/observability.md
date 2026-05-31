# Observability

The backend emits **structured logs**, **metrics**, and **traces** so that an
agent (or human) can reproduce and diagnose a bug from its signals. Wiring lives
in `back/app/settings/logging.py` and `back/app/settings/observability.py`; all
of it is controlled by settings in `back/app/settings/config.py` (env-overridable).

## Settings / env vars

| Env var | Default | Effect |
| ------- | ------- | ------ |
| `LOG_LEVEL` | `INFO` | stdlib + structlog level |
| `LOG_JSON` | `false` | `true` → single-line JSON logs (prod); else colored console |
| `METRICS_ENABLED` | `true` | expose `GET /metrics` (Prometheus) |
| `OTEL_ENABLED` | `false` | enable OpenTelemetry tracing |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | _unset_ | when set, export spans via OTLP; else print to console |
| `SERVICE_NAME` | `creature-api` | service name on traces |

## Logs

- `structlog` renders both structlog and stdlib `logging` records through one
  pipeline, so existing `logging.getLogger(__name__)` calls are formatted too.
- **Correlation IDs**: `asgi-correlation-id` attaches an `X-Request-ID` to each
  HTTP request and binds it into the log context; the websocket layer binds
  `room_id`, `player_id`, and `game_id` around engine processing
  (`app/websocket/room_manager.py`). Filter a whole request or game by one id.

```bash
LOG_JSON=true LOG_LEVEL=DEBUG make run
# {"event": "...", "level": "info", "correlation_id": "…", "timestamp": "…"}
```

## Metrics

`prometheus-fastapi-instrumentator` exposes `GET /metrics` with default HTTP
latency/throughput series. Scrape it from Prometheus, or just `curl localhost:8000/metrics`.

## Traces

FastAPI is auto-instrumented and the engine path adds an explicit
`engine.process_action` span (set in `room_manager`). Enable and view locally:

```bash
OTEL_ENABLED=true make run     # spans print to the console (SimpleSpanProcessor)
```

To export to a collector (Jaeger/Tempo/etc.) instead:

```bash
OTEL_ENABLED=true OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318/v1/traces make run
```

Tracing is **off by default** so local runs need no collector and tests stay
quiet (the OTel API is a no-op when no provider is configured).

## Follow-ups

Custom metric counters (actions processed, validation failures, game outcomes)
and richer engine spans are tracked in [`../harness.md`](../harness.md).
