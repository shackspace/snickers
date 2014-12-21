#!/bin/sh
cd "$(dirname "$(readlink -f "$0")")"
while sleep 1;do
  ./parse_rtl.py
done
