# embedding_service.py

from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from torchvision import models, transforms
from PIL import Image
from typing import List
import torch
import io

app = FastAPI()

# Carica modello pre-addestrato
model = models.mobilenet_v2(pretrained=True)
model.classifier = torch.nn.Identity()
model.eval()

# Preprocessing
preprocess = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])

class EmbeddingResponse(BaseModel):
    embedding: List[float]

@app.post("/embedding", response_model=EmbeddingResponse)
async def generate_embedding(image: UploadFile = File(...)):
    try:
        contents = await image.read()
        img = Image.open(io.BytesIO(contents)).convert("RGB")
        input_tensor = preprocess(img).unsqueeze(0)

        with torch.no_grad():
            embedding = model(input_tensor).squeeze(0).tolist()

        return EmbeddingResponse(embedding=embedding)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
