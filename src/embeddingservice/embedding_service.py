# embedding_service.py

from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
import torch
from transformers import AutoTokenizer, AutoModel

app = FastAPI()

# Carica modello e tokenizer (esempio con modello SentenceTransformers)
tokenizer = AutoTokenizer.from_pretrained("/app/model")
model = AutoModel.from_pretrained("/app/model")


class EmbeddingRequest(BaseModel):
    text: str

class EmbeddingResponse(BaseModel):
    embedding: List[float]

def mean_pooling(model_output, attention_mask):
    token_embeddings = model_output[0]  # first element of output contains token embeddings
    input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
    return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)

@app.post("/embedding", response_model=EmbeddingResponse)
def generate_embedding(req: EmbeddingRequest):
    encoded_input = tokenizer(req.text, padding=True, truncation=True, return_tensors='pt')
    with torch.no_grad():
        model_output = model(**encoded_input)
    embedding = mean_pooling(model_output, encoded_input['attention_mask'])
    embedding = embedding[0].tolist()
    return EmbeddingResponse(embedding=embedding)
