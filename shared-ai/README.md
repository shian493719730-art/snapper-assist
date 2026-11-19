# Snapper Assist shared AI relay

This service provides invitation-based access for the native helper. The current deployment has model billing disabled and zero spending allowances. It does not expose Codex, user shells, tools, arbitrary upstream URLs, or provider credentials to invitation holders.

Run the no-model checks with `node --test test/shared.test.mjs`, then `bash scripts/build.sh` and `node scripts/validate-artifact.mjs`. Node 24 is used for the SQLite-backed D1 test adapter. SQL triggers make budget checks and reservations atomic. Published migrations under `drizzle/` are immutable; append a migration for later schema changes. Runtime schema creation is not used.

Sites hosts the Worker and D1, with its identity recorded in `.openai/hosting.json`. Runtime secrets `ADMIN_TOKEN` and `PROVIDER_MASTER_KEY` are configured through Sites. `BILLING_ENABLED=false` is independent of invitations and database limits. Provider credentials are owner-enrolled over HTTPS and sealed with AES-GCM in D1; credentials, invitation codes, request text and result text are excluded from source and the desktop installer.

The owner-only `/admin/provider-check` reads the upstream model catalog without model generation. Worker requests use manual redirect handling and reject redirects rather than forwarding Authorization. Cloudflare Workers does not support the Fetch `redirect: error` mode; see its [Request API](https://developers.cloudflare.com/workers/runtime-apis/request/).

See the [product setup and data boundaries](../docs/shared-ai.zh-CN.md). Production enablement requires separate budget approval, verified model pricing and paid-path verification. The current change does not enable billing.
