# -------- STAGE 1: Build --------
FROM golang:1.22 as builder

WORKDIR /app

# Copia i go.mod e go.sum per scaricare le dipendenze
COPY go.mod go.sum ./
RUN go mod download

# Copia l'intero codice sorgente del servizio
COPY . .

# Compila il binario
RUN CGO_ENABLED=0 GOOS=linux GOARCH=arm64 go build -o productmanagementserver productmanagementserver.go

# -------- STAGE 2: Runtime --------
FROM gcr.io/distroless/base-debian11

WORKDIR /app

# Copia il binario da builder
COPY --from=builder /app/productmanagementserver .

# Aggiungi certificati CA (necessari per chiamate sicure o gRPC-TLS)
COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/

# Espone la porta gRPC (quella definita in productmanagementserver)
EXPOSE 3560

# Esegui il server
CMD ["./productmanagementserver"]
