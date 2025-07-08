package main

import (
	"context"
	"database/sql"
	"fmt"
	_ "reflect"
	_ "io/ioutil"
	"log"
	 "net"
  "os" 
	_ "encoding/base64"
	 "google.golang.org/grpc"
	 "google.golang.org/grpc/credentials/insecure"
	"github.com/pgvector/pgvector-go"

  pb "github.com/DamianoSamperi/microservices-demo-local/src/productmanagementservice/genproto"
	embedpb "github.com/DamianoSamperi/microservices-demo-local/src/embeddingservice/genproto"

	_ "github.com/jackc/pgx/v5/stdlib"
)

const (
	port              = ":3560"
	embeddingSvcAddr  = "embeddingservice:50051" // indirizzo microservizio embedding
	postgresConnStr   = "postgresql://user:password@localhost:5432/yourdb?sslmode=disable"
	embeddingDim      = 384
)

type server struct {
	pb.UnimplementedProductManagementServiceServer
	db            *sql.DB
	embeddingClient embedpb.EmbeddingServiceClient
}

func (s *server) AddProduct(ctx context.Context, req *pb.AddProductRequest) (*pb.AddProductResponse, error) {
	// 1. Leggi immagine dal path
	//imageBytes, err := ioutil.ReadFile(req.Picture)
	//if err != nil {
	//	return &pb.AddProductResponse{Success: false, Message: "cannot read image: " + err.Error()}, nil
	//}

	// 2. Codifica immagine in base64
	//imageB64 := base64.StdEncoding.EncodeToString(imageBytes)

	// 3. Chiama il servizio di embedding 
	embedResp, err := s.embeddingClient.GenerateEmbedding(ctx, &embedpb.EmbeddingRequest{
		Image: req.Picture,
	})

	if err != nil {
		return &pb.AddProductResponse{Success: false, Message: "embedding service error: " + err.Error()}, nil
	}

	embedding := embedResp.Embedding
	

	if err != nil {
			return nil, fmt.Errorf("embedding failed: %v", err)
	}
	// 4. Prepara l'embedding come array Postgres
	vector := pgvector.NewVector(embedding) 
	//embeddingStr := "{" // Postgres array literal
	//for i, v := range embedding {
	//	embeddingStr += fmt.Sprintf("%f", v)
	//	if i < len(embedding)-1 {
	//		embeddingStr += ","
	//	}
	//}
	//embeddingStr += "}"

	// 5. Inserimento nel DB

	imagePath := "static/img/products/" + req.Name + ".jpg"
	query := `
		INSERT INTO catalog_items
			(id, name, description, picture, price_usd_currency_code, price_usd_units, price_usd_nanos, categories, product_embedding, embed_model)
		VALUES
			($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)
	`
	_, err = s.db.ExecContext(ctx, query,
		req.Id, req.Name, req.Description, imagePath,
		req.PriceUsdCurrencyCode, req.PriceUsdUnits, req.PriceUsdNanos,
		req.Categories, vector, "mobilenet-v2",
	)
	if err != nil {
    return &pb.AddProductResponse{Success: false, Message: "image upload error: " + err.Error()}, nil
}

	return &pb.AddProductResponse{Success: true, Message: "product added", Id: req.Id}, nil
}
func (s *server) DeleteProduct(ctx context.Context, req *pb.DeleteProductRequest) (*pb.DeleteProductResponse, error) {
	// Esegui DELETE dal database
	query := `DELETE FROM catalog_items WHERE id = $1`
	result, err := s.db.ExecContext(ctx, query, req.Id)
	if err != nil {
		return &pb.DeleteProductResponse{Success: false, Message: "DB error: " + err.Error()}, nil
	}

	rowsAffected, err := result.RowsAffected()
	if err != nil {
		return &pb.DeleteProductResponse{Success: false, Message: "Error checking rows affected: " + err.Error()}, nil
	}

	if rowsAffected == 0 {
		return &pb.DeleteProductResponse{Success: false, Message: "No product found with given ID"}, nil
	}

	return &pb.DeleteProductResponse{Success: true, Message: "Product deleted successfully"}, nil
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
	//conn, err := grpc.Dial(embeddingSvcAddr, grpc.WithInsecure())
	conn, err := grpc.Dial(embeddingSvcAddr, grpc.WithTransportCredentials(insecure.NewCredentials()))
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

