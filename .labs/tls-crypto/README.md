# TLS & Cryptography Lab (OpenSSL CLI)

Hands-on path from crypto primitives → your own CA → a live TLS handshake →
breaking validation and requiring mutual TLS. Everything is inspectable; nothing
is magic by the end.

## Prerequisites

- **OpenSSL** — ships with Git for Windows (`openssl version` to check; you want 1.1.1+ or 3.x).
- Run the scripts from **Git Bash**.
- Optional: **Wireshark/tshark** to watch raw handshake bytes in stage 3.

All generated keys & certs land in `./out/` (gitignored — they contain private keys).

## Run order

```bash
cd .labs/tls-crypto
sh 01-primitives.sh        # keys, hashing, HMAC, signatures, encryption
sh 02-build-ca.sh          # root -> intermediate -> leaf, verify the chain
sh 03-serve-and-inspect.sh # serve TLS, dissect the handshake
sh 04-break-and-mtls.sh    # untrusted issuer, SAN mismatch, mutual TLS
```

Stages 3 and 4 depend on the certs from stage 2.

## What to actually look at

| Stage | The lesson |
|-------|-----------|
| 1 | Confidentiality (encryption) vs integrity (hash) vs authenticity (HMAC/signature) are *separate* problems with *separate* tools. |
| 2 | A certificate is a **public key + identity, signed by a CA**. Trust chains: leaf → intermediate → root. `basicConstraints`, `keyUsage`, `SAN` are what make a cert valid for a purpose. |
| 3 | The handshake: cert chain presented, version + cipher negotiated, `Verify return code 0`. TLS 1.3 + an ECDHE cipher = **forward secrecy**. |
| 4 | *Why* connections fail: untrusted issuer, hostname/SAN mismatch (a valid cert for the wrong name is still rejected), and **mTLS** where the client must also prove identity. |

## Inspect commands worth memorizing

```bash
openssl x509 -in out/server.crt -noout -text          # full cert
openssl x509 -in out/server.crt -noout -ext subjectAltName
openssl verify -CAfile out/root-ca.crt -untrusted out/intermediate.crt out/server.crt
openssl s_client -connect host:443 -servername host    # probe any real server
```

## Where this shows up in your other work

This is exactly what **cert-manager** automates in Kubernetes: it runs a CA (or
talks ACME/Let's Encrypt), issues leaf certs, and mounts the chain into pods —
stages 2–3 done for you. **mTLS** (stage 4) is how service meshes (Istio/Linkerd)
authenticate pod-to-pod traffic. Having built it by hand once, the k8s
abstractions stop being opaque.
