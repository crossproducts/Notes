#!/usr/bin/env sh
# Stage 3: Serve TLS with your leaf cert and dissect the handshake.
# Run 02-build-ca.sh first.
set -eu
OUT=./out
cd "$OUT"
PORT=4433

echo "Starting TLS server on :$PORT (leaf + intermediate via -cert_chain)..."
# s_server -cert sends ONLY the leaf; -cert_chain adds the intermediate so the
# client can build leaf -> intermediate -> root. Without it: "code 21".
openssl s_server -accept "$PORT" -cert server.crt -key server.key -cert_chain intermediate.crt -www \
  > s_server.log 2>&1 &
SRV=$!
trap 'kill "$SRV" 2>/dev/null' EXIT
sleep 1

echo; echo "== Certificate chain the server presented (client view) =="
openssl s_client -connect localhost:$PORT -CAfile root-ca.crt -servername localhost </dev/null 2>/dev/null \
  | sed -n '/Certificate chain/,/^---/p'

echo "== Negotiated protocol, cipher, and verification result =="
openssl s_client -connect localhost:$PORT -CAfile root-ca.crt -servername localhost </dev/null 2>/dev/null \
  | grep -E "Protocol|Cipher    |Verify return code"
echo "(Verify return code 0 = ok. TLS 1.3 + an ECDHE cipher = forward secrecy.)"

echo; echo "Go deeper:"
echo "  - Force a version:   openssl s_client -connect localhost:$PORT -tls1_2   (vs -tls1_3)"
echo "  - Capture raw bytes: tshark -i lo -f 'tcp port $PORT' -Y tls.handshake"
echo "    then look at ClientHello / ServerHello / Certificate / key exchange."
