#!/usr/bin/env sh
# Stage 1: Crypto primitives — keys, hashing, HMAC, signatures, encryption.
# Goal: feel that confidentiality, integrity, and authenticity are DIFFERENT
# things, solved by different primitives. Nothing here involves TLS yet.
set -eu
OUT=./out
mkdir -p "$OUT"
cd "$OUT"
MSG="the quick brown fox"

echo "== 1. Keypairs (asymmetric: a private key + a derived public key) =="
openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:2048 -out demo-rsa.key
openssl pkey -in demo-rsa.key -pubout -out demo-rsa.pub
openssl genpkey -algorithm EC -pkeyopt ec_paramgen_curve:P-256 -out demo-ec.key
openssl pkey -in demo-ec.key -pubout -out demo-ec.pub
echo "Generated RSA-2048 and EC P-256 keypairs (EC is smaller for the same strength)."

echo; echo "== 2. Hashing — integrity only (no key) =="
printf '%s' "$MSG" | openssl dgst -sha256

echo; echo "== 3. HMAC — integrity + authenticity from a SHARED secret =="
printf '%s' "$MSG" | openssl dgst -sha256 -hmac "shared-secret"

echo; echo "== 4. Digital signature — authenticity from a PRIVATE key, anyone verifies =="
printf '%s' "$MSG" > msg.txt
openssl dgst -sha256 -sign demo-rsa.key -out msg.sig msg.txt
openssl dgst -sha256 -verify demo-rsa.pub -signature msg.sig msg.txt   # prints "Verified OK"

echo; echo "== 5. Symmetric encryption — confidentiality, one shared password (AES-256-CBC) =="
openssl enc -aes-256-cbc -pbkdf2 -salt -in msg.txt -out msg.enc -pass pass:hunter2
printf 'decrypted: '; openssl enc -d -aes-256-cbc -pbkdf2 -in msg.enc -pass pass:hunter2

echo; echo "== 6. Asymmetric encryption — RSA, small payloads only (this is why TLS uses it just to bootstrap) =="
printf '%s' "$MSG" | openssl pkeyutl -encrypt -pubin -inkey demo-rsa.pub -out msg.rsa
printf 'RSA-decrypted: '; openssl pkeyutl -decrypt -inkey demo-rsa.key -in msg.rsa; echo

echo; echo "Takeaway: hash != HMAC != signature != encryption. TLS combines all of them."
