package main

import (
	"context"
	"database/sql"
	"fmt"
	"log"
	"net"
        "os" 
	"google.golang.org/grpc"
	pb "productmanagementservice/genproto"
	embedpb "embeddingservice/genproto"

	_ "github.com/jackc/pgx/v5/stdlib"
)

const (
	port              = ":3560"
	embeddingSvcAddr  = "localhost:3570" // indirizzo microservizio embedding
	postgresConnStr   = "postgresql://user:password@localhost:5432/yourdb?sslmode=disable"
	embeddingDim      = 384
)

type server struct {
	pb.UnimplementedProductManagementServiceServer
	db            *sql.DB
	embeddingClient embedpb.EmbeddingServiceClient
}

func (s *server) AddProduct(ctx context.Context, req *pb.AddProductRequest) (*pb.AddProductResponse, error) {
	// Genera embedding
	textToEmbed := req.Name + " " + req.Description

	embedResp, err := s.embeddingClient.GenerateEmbedding(ctx, &embedpb.GenerateEmbeddingRequest{Text: textToEmbed})
	if err != nil {
		return &pb.AddProductResponse{Success: false, Message: "embedding service error: " + err.Error()}, nil
	}

	embedding := embedResp.Embedding

	// Convert embedding []float32 in formato adatto a postgres vector (float8[])
	// Nota: la tua colonna è vector(384), quindi array di 384 float8. PG driver deve supportarlo
	// Spesso si può fare passando come []byte o come array testo. Qui useremo array testuale

	embeddingStr := "{" // Postgres array literal
	for i, v := range embedding {
		embeddingStr += fmt.Sprintf("%f", v)
		if i < len(embedding)-1 {
			embeddingStr += ","
		}
	}
	embeddingStr += "}"

	// Inserisci nel DB
	query := `
		INSERT INTO catalog_items
			(id, name, description, picture, price_usd_currency_code, price_usd_units, price_usd_nanos, categories, product_embedding, embed_model)
		VALUES
			($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)
	`

	_, err = s.db.ExecContext(ctx, query,
		req.Id, req.Name, req.Description, req.Picture,
		req.PriceUsdCurrencyCode, req.PriceUsdUnits, req.PriceUsdNanos,
		req.Categories, embeddingStr, "your-embedding-model",
	)
	if err != nil {
		return &pb.AddProductResponse{Success: false, Message: "db insert error: " + err.Error()}, nil
	}

	return &pb.AddProductResponse{Success: true, Message: "product added"}, nil
}

func main() {
        postgresConnStr := fmt.Sprintf(
	    "postgresql://%s:%s@%s:%s/%s?sslmode=disable",
	    os.Getenv("PG_USER"),
	    os.Getenv("PG_PASSWORD"),
	    os.Getenv("PG_HOST"),
	    os.Getenv("PG_PORT"),
	    os.Getenv("PG_DB"),
        )
	// Connessione a Postgres
	db, err := sql.Open("pgx", postgresConnStr)
	if err != nil {
		log.Fatalf("failed to connect to db: %v", err)
	}
	defer db.Close()

	// Connessione gRPC microservizio embedding
	conn, err := grpc.Dial(embeddingSvcAddr, grpc.WithInsecure())
	if err != nil {
		log.Fatalf("failed to connect to embedding service: %v", err)
	}
	defer conn.Close()

	embeddingClient := embedpb.NewEmbeddingServiceClient(conn)

	lis, err := net.Listen("tcp", port)
	if err != nil {
		log.Fatalf("failed to listen: %v", err)
	}

	s := grpc.NewServer()
	srv := &server{
		db:              db,
		embeddingClient: embeddingClient,
	}

	pb.RegisterProductManagementServiceServer(s, srv)

	log.Printf("product management server listening at %v", lis.Addr())

	if err := s.Serve(lis); err != nil {
		log.Fatalf("failed to serve: %v", err)
	}
}

