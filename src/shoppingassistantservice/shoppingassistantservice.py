#!/usr/bin/env python3
import os
import torch
import requests
import json
from flask import Flask, request
from urllib.parse import unquote
from PIL import Image
from transformers import AutoTokenizer, AutoModelForCausalLM, BlipProcessor, BlipForConditionalGeneration
from sentence_transformers import SentenceTransformer
import psycopg2
import traceback

# ============ SETUP ============

# Device config
device = "cuda" if torch.cuda.is_available() else "cpu"
revision = "c0fdd15a9e3b8ed1a2f47c882e1723d9a3f87c3b"
print(device,flush=True)
# LLM: leggero, adatto a Jetson
#model_name = "microsoft/Phi-3.5-mini-instruct"
#tokenizer = AutoTokenizer.from_pretrained(model_name)
#llm = AutoModelForCausalLM.from_pretrained(model_name, device_map="cuda",torch_dtype="auto",trust_remote_code=True,attn_implementation="eager")
model_path = "/root/.cache/huggingface/my_local_model"
tokenizer = AutoTokenizer.from_pretrained(model_path)
llm = AutoModelForCausalLM.from_pretrained(model_path, device_map="cuda", torch_dtype="auto", trust_remote_code=True,attn_implementation="eager")
# Embedding model (384 dim)
embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
#phi_pipe = pipeline(
#    "text-generation",
#    model=llm,
#    tokenizer=phi_tokenizer,
#)
#pipeline = TextGenerationPipeline(
#    model=model,
#    tokenizer=tokenizer,
#    device=0 if torch.cuda.is_available() else -1,
#)
# Image captioning with BLIP
blip_processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
blip_model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base").to(device)

# PostgreSQL + pgvector
PGPASSWORD = os.environ.get("PGPASSWORD", "yourlocalpassword")
conn = psycopg2.connect(
    dbname="products",
    user="postgres",
    password=PGPASSWORD,
    host=os.environ.get("DB_HOST", "postgres")
)

# ============ HELPER FUNCTIONS ============

def describe_image(image_url):
    try:
        raw_image = Image.open(requests.get(image_url, stream=True).raw).convert('RGB')
        inputs = blip_processor(raw_image, return_tensors="pt").to(device)
        out = blip_model.generate(**inputs)
        return blip_processor.decode(out[0], skip_special_tokens=True)
    except Exception as e:
        print("Errore nella descrizione immagine:", e, flush=True)
        return "modern room with neutral tones"

SYSTEM = (
    "Tu sei un assistente per lo shopping online. "
    "Rispondi in modo naturale e utile, suggerendo prodotti se serve. "
    "Non ripetere il prompt, non aggiungere prefissi come “Response:” o “Assistente:”."
)
def llm_generate(user_message):
    generation_args = {
    "max_new_tokens": 80,
    "temperature": 0.5,
    "do_sample": True,
    "pad_token_id":tokenizer.eos_token_id
    }
    # 1) costruisco prompt
    messages = [
        {"role": "system",    "content": SYSTEM},
        {"role": "user",      "content": user_message}
    ]
    prompt = ""
    for msg in messages:
        role = msg["role"]
        content = msg["content"]
        if role == "user":
            prompt += f"<|user|>\n{content}\n"
        elif role == "assistant":
            prompt += f"<|assistant|>\n{content}\n"
    prompt += "<|assistant|>\n"
    inputs = tokenizer(prompt, return_tensors="pt").to(llm.device)
    input_len = inputs['input_ids'].shape[-1]
    #prompt = SYSTEM + "\nUtente: " + user_message + "\nAssistente:"
    #input_ids = tokenizer.encode(prompt, return_tensors="pt").to(device)
    #input_len = input_ids.shape[-1]

    # 2) genero
    #eos = tokenizer.eos_token_id or tokenizer.pad_token_id or 50256
    outputs = llm.generate(**inputs,**generation_args)
    #output = pipeline(messages, **generation_args)
    # 3) taglio via i token del prompt
    #gen_ids = output_ids[input_len:]
    #result = tokenizer.decode(gen_ids, skip_special_tokens=True).strip()
    #result = output[0]['generated_text']
    #return result
    output_ids = outputs[0][input_len:]
    generated_response = tokenizer.decode(output_ids, skip_special_tokens=True).strip()
    #generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
    #generated_response = generated_text[len(prompt):].strip()

    return generated_response


# ============ FLASK APP ============

app = Flask(__name__)
import logging
logging.basicConfig(level=logging.DEBUG)

@app.route("/", methods=["POST"])
def recommend():
    try:
        prompt = unquote(request.json["message"])
#        image_url = request.json["image"]
        image_url = request.json.get("image")

        # Step 1 – Describe the room
        if image_url:
           room_description = describe_image(image_url)
           # Step 2 – Create embedding for query
           query = f"{prompt}. Room style: {room_description}"
           embedding = embedding_model.encode(query).tolist()

           # Step 3 – pgvector similarity search
           try:
               with conn.cursor() as cur:
                   cur.execute("""
                       SELECT id, name, description, categories
                       FROM catalog_items
                       ORDER BY product_embedding <->  CAST(%s AS vector) LIMIT 5
                   """, (embedding,))
                   rows = cur.fetchall()
           except Exception as e:
               conn.rollback()
               print("❌ Errore durante la query:", e)
               return {"error": f"Errore nella query: {e}"}, 500
        else:
            room_description = None
            rows=None
        if not rows:
            print("💡 Nessun prodotto trovato: passo a modalità chat semplice", flush=True)
            # Modalità chatbot fallback
           # chat_prompt = (
           #     f"L'utente ha scritto: “{prompt}”\n"
           #     "Adesso tu rispondi come un assistente per lo shopping online, *solo* il testo della risposta, "
           #     "senza aggiungere alcun prefisso come “Assistente:”, “response:” o simili."
           # )
            chat_prompt=prompt
            response = llm_generate(chat_prompt)
            return {"content": response}, 200

        relevant = [{"id": r[0], "name": r[1], "description": r[2], "categories": r[3]} for r in rows]

        # Step 4 – Prompt final LLM
        relevant_text = "\n".join([f"{r['name']}: {r['description']}" for r in relevant])
        room_part = f"Room style: {room_description}\n" if room_description else ""
        final_prompt = (
            f"{room_part}"
            f"User write: {prompt}\n"
            f"Relevant products:\n{relevant_text}\n"
            f"Respond naturally and helpfully, like an online shopping assistant, suggesting products if appropriate"
        )
        print("🧠 Prompt finale:", final_prompt, flush=True)
        result = llm_generate(final_prompt)
        print("🧾 Output raw:", result, flush=True)
        return {"content": result}, 200
    except Exception as e:
        print("❌ Errore interno:", e, flush=True)
        traceback.print_exc()  # <- stampa lo stack trace
        return {"error": str(e)}, 500

# ============ MAIN ============

if __name__ == "__main__":
    print("🔁 Starting Shopping Assistant Service on port 8080", flush=True)
    app.run(host="0.0.0.0", port=8080)
