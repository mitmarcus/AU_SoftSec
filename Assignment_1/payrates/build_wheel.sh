#!/bin/sh
# builds the payrates wheel and pins its hash for payroll
set -e
cd "$(dirname "$0")/.."

rm -f wheels/payrates-*.whl
pip wheel --no-deps -w wheels ./payrates

WHEEL=$(ls wheels/payrates-*.whl)
HASH=$(sha256sum "$WHEEL" | cut -d' ' -f1)
echo "payrates @ file:///$WHEEL --hash=sha256:$HASH" > payroll/payrates.txt
cat payroll/payrates.txt
