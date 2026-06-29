#!/usr/bin/env sh
# Stage 4: Break validation on purpose, then require mutual TLS.
# Run 02-build-ca.sh first. Each section starts a server, probes it, kills it.
set -eu
# Git Bash on Windows rewrites a leading "/" in -subj into a path; disable that.
export MSYS_NO_PATHCONV=1
OUT=./out
cd "$OUT"
PORT=4433

start_server() {  # $1 = leaf cert, $2 = key, $3 = intermediate chain, $4.. = extra args
  cert="$1"; key="$2"; chain="$3"; shift 3
  # -cert_chain sends the intermediate too, so the client can reach the root.
  openssl s_server -accept "$PORT" -cert "$cert" -key "$key" -cert_chain "$chain" -www "$@" \
    > s_server.log 2>&1 &
  SRV=$!
  sleep 1
}
stop_server() { kill "$SRV" 2>/dev/null || true; }

echo "############ 1. Untrusted issuer ############"
echo "Client does NOT supply our root CA -> chain can't be built:"
start_server server.crt server.key intermediate.crt
openssl s_client -connect localhost:$PORT -servername localhost </dev/null 2>/dev/null \
  | grep -E "Verify return code"
stop_server
echo "(expect: 'unable to get local issuer certificate')"

echo; echo "############ 2. Hostname / SAN mismatch ############"
# Mint a cert whose SAN is for a DIFFERENT host, signed by our (trusted) CA.
openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:2048 -out wrong.key
openssl req -new -key wrong.key -subj "/CN=evil.example.com" -out wrong.csr
cat > wrong.ext <<'EOF'
basicConstraints=CA:FALSE
extendedKeyUsage=serverAuth
subjectAltName=DNS:evil.example.com
EOF
openssl x509 -req -in wrong.csr -CA intermediate.crt -CAkey intermediate.key \
  -CAcreateserial -sha256 -days 365 -extfile wrong.ext -out wrong.crt
echo "Chain is trusted, but the name doesn't match 'localhost':"
start_server wrong.crt wrong.key intermediate.crt
openssl s_client -connect localhost:$PORT -CAfile root-ca.crt -servername localhost \
  -verify_hostname localhost </dev/null 2>/dev/null | grep -E "Verify return code"
stop_server
echo "(expect: 'Hostname mismatch', verify code 62 — why a valid cert still gets rejected)"

echo; echo "############ 3. Mutual TLS (server requires a client cert) ############"
openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:2048 -out client.key
openssl req -new -key client.key -subj "/CN=test-client" -out client.csr
cat > client.ext <<'EOF'
basicConstraints=CA:FALSE
extendedKeyUsage=clientAuth
EOF
openssl x509 -req -in client.csr -CA intermediate.crt -CAkey intermediate.key \
  -CAcreateserial -sha256 -days 365 -extfile client.ext -out client.crt
cat root-ca.crt intermediate.crt > ca-bundle.pem

echo "-- Without a client cert: server rejects --"
# Force TLS 1.2 here: under TLS 1.3 the server rejects asynchronously and the
# client can't see it; under 1.2 the handshake fails synchronously and visibly.
start_server server.crt server.key intermediate.crt -Verify 1 -CAfile ca-bundle.pem
openssl s_client -connect localhost:$PORT -CAfile root-ca.crt -servername localhost -tls1_2 </dev/null 2>&1 \
  | grep -E "alert|handshake failure|peer did not return|Verify return code" | head -2 \
  || echo "  (handshake failed, as expected)"
stop_server

echo "-- With the client cert: handshake succeeds --"
start_server server.crt server.key intermediate.crt -Verify 1 -CAfile ca-bundle.pem
openssl s_client -connect localhost:$PORT -CAfile root-ca.crt -servername localhost \
  -cert client.crt -key client.key </dev/null 2>/dev/null | grep -E "Verify return code"
stop_server

echo; echo "Exercise: mint an EXPIRED leaf and watch verify fail."
echo "  OpenSSL 3:  openssl x509 -req ... -not_before 20200101000000Z -not_after 20200102000000Z"
