Drop your wildcard cert/key pair here (gitignored, not committed):

- `labzs.com.crt` — full chain (leaf + intermediates)
- `labzs.com.key` — private key

Traefik picks these up automatically via `traefik/dynamic/tls.yml` and serves
them as the default certificate on the `websecure` (:443) entrypoint. No
restart needed for renewals — the file provider watches for changes.
