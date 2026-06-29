#!/usr/bin/env sh
# Stage 2: Build a CA hierarchy (root -> intermediate -> leaf) and verify the chain.
# This is the heart of TLS: X.509 certificates and the chain of trust.
set -eu
# Git Bash on Windows rewrites a leading "/" in -subj into a path; disable that.
export MSYS_NO_PATHCONV=1
OUT=./out
mkdir -p "$OUT"
cd "$OUT"

echo "== Root CA (self-signed; the trust anchor) =="
# Self-sign via CSR + x509 -req (NOT req -x509) so we control extensions exactly —
# req -x509 also injects basicConstraints from openssl.cnf, producing a malformed
# cert with a DUPLICATE extension that won't load as a trust anchor.
openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:4096 -out root-ca.key
openssl req -new -key root-ca.key \
  -subj "/C=US/O=Notes Lab/CN=Notes Lab Root CA" -out root-ca.csr
cat > root-ca.ext <<'EOF'
basicConstraints=critical,CA:TRUE
keyUsage=critical,keyCertSign,cRLSign
subjectKeyIdentifier=hash
EOF
openssl x509 -req -in root-ca.csr -signkey root-ca.key -sha256 -days 3650 \
  -extfile root-ca.ext -out root-ca.crt

echo "== Intermediate CA (signed by root; pathlen:0 = cannot mint further CAs) =="
openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:4096 -out intermediate.key
openssl req -new -key intermediate.key \
  -subj "/C=US/O=Notes Lab/CN=Notes Lab Intermediate CA" -out intermediate.csr
cat > intermediate.ext <<'EOF'
basicConstraints=critical,CA:TRUE,pathlen:0
keyUsage=critical,keyCertSign,cRLSign
subjectKeyIdentifier=hash
authorityKeyIdentifier=keyid:always
EOF
openssl x509 -req -in intermediate.csr -CA root-ca.crt -CAkey root-ca.key \
  -CAcreateserial -sha256 -days 1825 -extfile intermediate.ext -out intermediate.crt

echo "== Server leaf cert (signed by intermediate; CN=localhost + SANs) =="
openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:2048 -out server.key
openssl req -new -key server.key -subj "/C=US/O=Notes Lab/CN=localhost" -out server.csr
cat > server.ext <<'EOF'
basicConstraints=CA:FALSE
keyUsage=critical,digitalSignature,keyEncipherment
extendedKeyUsage=serverAuth
subjectAltName=DNS:localhost,IP:127.0.0.1
subjectKeyIdentifier=hash
authorityKeyIdentifier=keyid,issuer
EOF
openssl x509 -req -in server.csr -CA intermediate.crt -CAkey intermediate.key \
  -CAcreateserial -sha256 -days 365 -extfile server.ext -out server.crt

# A TLS server presents leaf + intermediate (NOT the root — clients already trust that).
cat server.crt intermediate.crt > server-fullchain.pem

echo; echo "== Verify the chain (root trusts intermediate trusts leaf) =="
openssl verify -CAfile root-ca.crt -untrusted intermediate.crt server.crt

echo; echo "Inspect any cert with, e.g.:"
echo "  openssl x509 -in out/server.crt -noout -text | less"
echo "  openssl x509 -in out/server.crt -noout -ext subjectAltName"
