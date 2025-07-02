package main

import (
	"context"
	"fmt"
	"log"
	"math/rand"
	"net"

	pb "path/to/your/generated/embeddingpb"

	"google.golang.org/grpc"
)

const (
	port           = ":50051"
	embeddingSize  = 384
)

type server struct {
	pb.UnimplementedEmbeddingServiceServer
}

// GenerateEmbedding genera un vettore embedding mock di 384 float casuali
func (s *server) GenerateEmbedding(ctx context.Context, req *pb.EmbeddingRequest) (*pb.EmbeddingResponse, error) {
	text := req.GetText()
	log.Printf("Generating embedding for text: %s", text)

	embedding := make([]float32, embeddingSize)
	for i := range embedding {
		embedding[i] = rand.Float32() // qui puoi integrare un modello vero
	}

	return &pb.EmbeddingResponse{Embedding: embedding}, nil
}

func main() {
	lis, err := net.Listen("tcp", port)
	if err != nil {
		log.Fatalf("failed to listen: %v", err)
	}

	s := grpc.NewServer()
	pb.RegisterEmbeddingServiceServer(s, &server{})
	fmt.Printf("Embedding service listening on %s\n", port)
	if err := s.Serve(lis); err != nil {
		log.Fatalf("failed to serve: %v", err)
	}
}
