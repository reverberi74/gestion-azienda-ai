import torch
from fastapi import FastAPI
from transformers import AutoTokenizer, AutoModel

print("Torch version:", torch.__version__)
print("FastAPI OK")
print("Transformers OK")