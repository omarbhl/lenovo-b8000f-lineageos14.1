#!/bin/bash
set -euo pipefail
if [ "$#" -ne 1 ]; then echo 'Usage: bash scripts/create_signing_key.sh PRIVATE_KEY_DIRECTORY' >&2; exit 2; fi
keys=$(realpath -m "$1")
mkdir -p "$keys"
for file in certificate.pem private.pem private.pk8; do
  if [ -e "$keys/$file" ]; then echo 'Refusing to replace existing signing material' >&2; exit 1; fi
done
umask 077
openssl genrsa -out "$keys/private.pem" 2048
openssl req -new -x509 -key "$keys/private.pem" -out "$keys/certificate.pem" -days 3650 -subj '/CN=B8000F Contributor Experimental/'
openssl pkcs8 -topk8 -inform PEM -outform DER -in "$keys/private.pem" -out "$keys/private.pk8" -nocrypt
openssl x509 -in "$keys/certificate.pem" -noout -fingerprint -sha256
echo 'Keep private.pem and private.pk8 local and outside Git. This is a new identity, not the original release key.'
