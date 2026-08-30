#!/usr/bin/env python
"""Run training and capture output."""
import subprocess
import sys

result = subprocess.run([
    sys.executable, 'train.py',
    '--data', 'data/archive_combined.csv',
    '--window-seconds', '30',
    '--sequence-length', '10',
    '--backbone', 'lstm',
    '--epochs', '5',
    '--patience', '2',
    '--batch-size', '32'
], cwd=r'C:\Users\mahes\Downloads\attack model')

print(f"\n\nTraining completed with exit code: {result.returncode}", flush=True)
sys.exit(result.returncode)
