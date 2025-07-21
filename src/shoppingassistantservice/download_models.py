from transformers import AutoTokenizer, AutoModelForCausalLM, BlipProcessor, BlipForConditionalGeneration
from sentence_transformers import SentenceTransformer

# Modello LLM
model_name = "microsoft/Phi-3.5-mini-instruct"
print("Scaricando modello LLM...")
AutoTokenizer.from_pretrained(model_name)
AutoModelForCausalLM.from_pretrained(model_name)

# Modello embedding
print("Scaricando modello embedding...")
SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

# Modello BLIP per captioning immagini
print("Scaricando modello BLIP...")
BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")

print("Download completato.")
