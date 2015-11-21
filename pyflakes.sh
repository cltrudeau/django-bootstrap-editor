#!/bin/bash

echo "============================================================"
echo "== pyflakes =="
pyflakes bseditor | grep -v migration
