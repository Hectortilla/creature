### What problem does this solve?


### How does this solve it?


## Checklist

- [ ] Backend gate green — `cd back && make check` (if `back/` changed)
- [ ] Frontend gate green — `npm run test && npm run deps:check && npm run build` (if `front/` changed); no new prettier/eslint/svelte-check violations
- [ ] Module boundaries respected — `make arch` passes; no new `ignore_imports` added to silence a violation
- [ ] No generated files hand-edited (`front/src/lib/api/*.gen.ts`, `front/src/lib/utils/generated/*`) — regenerated via `npm run generate` if the API changed
- [ ] Docs updated (`AGENTS.md` / `docs/`) if behaviour, commands, or structure changed
