#!/bin/bash

# Avvia il server Python FastAPI in background
echo "Starting Python FastAPI server..."
python3 -m uvicorn embedding_service:app --host 0.0.0.0 --port 8000 &

PYTHON_PID=$!

# Funzione per controllare se la porta 8000 è attiva
function wait_for_python() {
  echo "Waiting for Python server to start..."
  until nc -z localhost 8000; do
    sleep 1
  done
  echo "Python server is up!"
}

wait_for_python

# Avvia il servizio Go (supponendo che il binario si chiami embeddingservice-go)
echo "Starting Go service..."
./embeddingservice-go

# Quando Go finisce, termina anche Python
kill $PYTHON_PID

