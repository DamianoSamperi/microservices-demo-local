package main

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net"
	"net/http"

	pb "github.com/DamianoSamperi/microservices-demo-local/src/embeddingservice/genproto"

	"google.golang.org/grpc"
)

const (
	port          = ":50051"
	pythonSvcURL  = "http://localhost:8000/embedding"
	embeddingSize = 384
)

type server struct {
	pb.UnimplementedEmbeddingServiceServer
}

type embeddingRequest struct {
	Text string `json:"text"`
}

type embeddingResponse struct {
	Embedding []float32 `json:"embedding"`
}

func (s *server) GenerateEmbedding(ctx context.Context, req *pb.EmbeddingRequest) (*pb.EmbeddingResponse, error) {
	// Recupera immagine
	imgBytes := req.GetImage()
	if len(imgBytes) == 0 {
		return nil, fmt.Errorf("image is empty")
	}
	// Prepara buffer per multipart/form-data
	var buf bytes.Buffer
	writer := multipart.NewWriter(&buf)

	part, err := writer.CreateFormFile("image", "image.jpg")
	if err != nil {
		return nil, fmt.Errorf("failed to create form file: %w", err)
	}

	_, err = part.Write(imgBytes)
	if err != nil {
		return nil, fmt.Errorf("failed to write image to form: %w", err)
	}

	err = writer.Close()
	if err != nil {
		return nil, fmt.Errorf("failed to close multipart writer: %w", err)
	}

  // Fai POST HTTP al servizio Python (che ora accetta multipart/form-data)
	httpResp, err := http.Post(pythonSvcURL, writer.FormDataContentType(), &buf)
	if err != nil {
		return nil, fmt.Errorf("failed to call python embedding service: %w", err)
	}
	defer httpResp.Body.Close()

	// Leggi la risposta
	body, err := io.ReadAll(httpResp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read python service response: %w", err)
	}

	if httpResp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("python service returned status %d: %s", httpResp.StatusCode, string(body))
	}

	var resp embeddingResponse
	if err := json.Unmarshal(body, &resp); err != nil {
		return nil, fmt.Errorf("failed to unmarshal python response: %w", err)
	}

	if len(resp.Embedding) != embeddingSize {
		return nil, fmt.Errorf("unexpected embedding size: got %d, want %d", len(resp.Embedding), embeddingSize)
	}

	return &pb.EmbeddingResponse{Embedding: resp.Embedding}, nil
}

func main() {
	lis, err := net.Listen("tcp", port)
	if err != nil {
		log.Fatalf("failed to listen: %v", err)
	}

	s := grpc.NewServer()
	pb.RegisterEmbeddingServiceServer(s, &server{})
	fmt.Printf("Embedding gRPC proxy service listening on %s\n", port)

	if err := s.Serve(lis); err != nil {
		log.Fatalf("failed to serve: %v", err)
	}
}
