# Generated artifacts

Reference copies of machine-generated artifacts, and notes on how to regenerate
them. **Do not hand-edit anything generated** — change the source and regenerate.

| Artifact | Source of truth | Regenerate |
| -------- | --------------- | ---------- |
| OpenAPI schema | backend routes (`back/app/routers/`) | served at `http://localhost:8000/openapi.json`; client built by `cd front && npm run generate-client` |
| Frontend API client (`front/src/lib/api/*.gen.ts`) | OpenAPI schema | `cd front && npm run generate-client` |
| Action metadata (`front/src/lib/utils/generated/*`) | backend action definitions | `cd front && npm run generate-action-metadata` |

`cd front && npm run generate` runs both client + action-metadata generation. The
generated frontend files are the **contract boundary** between backend and
frontend — see [`../architecture.md`](../architecture.md).
