// Copyright 2024 Google LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//      https://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

package main

import (
	"bytes"
	"context"
	"fmt"
	"net"
	"os"
	"strings"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
	
	"cloud.google.com/go/alloydbconn"
	secretmanager "cloud.google.com/go/secretmanager/apiv1"
	"cloud.google.com/go/secretmanager/apiv1/secretmanagerpb"
	pb "github.com/GoogleCloudPlatform/microservices-demo/src/productcatalogservice/genproto"
	productpb "github.com/DamianoSamperi/microservices-demo-local/src/productmanagementservice/genproto"
	"github.com/golang/protobuf/jsonpb"
	"github.com/jackc/pgx/v5/pgxpool"
)

func loadCatalog(catalog *pb.ListProductsResponse) error {
	catalogMutex.Lock()
	defer catalogMutex.Unlock()
	conn, err := grpc.Dial("productmanagementservice:3560", grpc.WithTransportCredentials(insecure.NewCredentials()))
  if err != nil {
	  log.Fatalf("failed to connect to productmanagementservice: %v", err)
  }
  defer conn.Close()
	productClient := productpb.NewProductManagementServiceClient(conn)

	if os.Getenv("ALLOYDB_CLUSTER_NAME") != "" {
		return loadCatalogFromAlloyDB(catalog)
	}
	if os.Getenv("USE_PG") == "true" {
    return loadCatalogFromPostgres(catalog,productClient)
 }

	return loadCatalogFromLocalFile(catalog)
}

func loadCatalogFromLocalFile(catalog *pb.ListProductsResponse) error {
	log.Info("loading catalog from local products.json file...")

	catalogJSON, err := os.ReadFile("products.json")
	if err != nil {
		log.Warnf("failed to open product catalog json file: %v", err)
		return err
	}

	if err := jsonpb.Unmarshal(bytes.NewReader(catalogJSON), catalog); err != nil {
		log.Warnf("failed to parse the catalog JSON: %v", err)
		return err
	}

	log.Info("successfully parsed product catalog json")
	return nil
}

func getSecretPayload(project, secret, version string) (string, error) {
	ctx := context.Background()
	client, err := secretmanager.NewClient(ctx)
	if err != nil {
		log.Warnf("failed to create SecretManager client: %v", err)
		return "", err
	}
	defer client.Close()

	req := &secretmanagerpb.AccessSecretVersionRequest{
		Name: fmt.Sprintf("projects/%s/secrets/%s/versions/%s", project, secret, version),
	}

	// Call the API.
	result, err := client.AccessSecretVersion(ctx, req)
	if err != nil {
		log.Warnf("failed to access SecretVersion: %v", err)
		return "", err
	}

	return string(result.Payload.Data), nil
}
func loadCatalogFromPostgres(catalog *pb.ListProductsResponse,productClient productpb.ProductManagementServiceClient) error {
	log.Info("loading catalog from standard PostgreSQL...")

	connStr := fmt.Sprintf(
	    "postgresql://%s:%s@%s:%s/%s?sslmode=disable",
	    os.Getenv("PG_USER"),
	    os.Getenv("PG_PASSWORD"),
	    os.Getenv("PG_HOST"),
	    os.Getenv("PG_PORT"),
	    os.Getenv("PG_DB"),
        )
	pool, err := pgxpool.New(context.Background(), connStr)
	if err != nil {
		return fmt.Errorf("failed to connect to db: %w", err)
	}
	defer pool.Close()

	query := "SELECT id, name, description, picture, price_usd_currency_code, price_usd_units, price_usd_nanos, categories FROM catalog_items"
	rows, err := pool.Query(context.Background(), query)
	if err != nil {
		return err
	}
	defer rows.Close()

	catalog.Products = catalog.Products[:0]
	for rows.Next() {
		product := &pb.Product{PriceUsd: &pb.Money{}}
		var categories string
		err := rows.Scan(&product.Id, &product.Name, &product.Description, &product.Picture, &product.PriceUsd.CurrencyCode, &product.PriceUsd.Units, &product.PriceUsd.Nanos, &categories)
		if err != nil {
			return err
		}
		if product.Picture == "" {
		  	_, err := productClient.DeleteProduct(context.Background(), &productpb.DeleteProductRequest{
		        Id: product.Id,
	       })
			  	if err != nil {
		         log.Errorf("Failed to delete product %s: %v", product.Id, err)
	        }
	        continue
		}	
		product.Categories = strings.Split(strings.ToLower(categories), ",")
    catalog.Products = append(catalog.Products, product)
	}

	log.Info("successfully loaded catalog from Postgres")
	return nil
}

func loadCatalogFromAlloyDB(catalog *pb.ListProductsResponse) error {
	log.Info("loading catalog from AlloyDB...")

	projectID := os.Getenv("PROJECT_ID")
	region := os.Getenv("REGION")
	pgClusterName := os.Getenv("ALLOYDB_CLUSTER_NAME")
	pgInstanceName := os.Getenv("ALLOYDB_INSTANCE_NAME")
	pgDatabaseName := os.Getenv("ALLOYDB_DATABASE_NAME")
	pgTableName := os.Getenv("ALLOYDB_TABLE_NAME")
	pgSecretName := os.Getenv("ALLOYDB_SECRET_NAME")

	pgPassword, err := getSecretPayload(projectID, pgSecretName, "latest")
	if err != nil {
		return err
	}

	dialer, err := alloydbconn.NewDialer(context.Background())
	if err != nil {
		log.Warnf("failed to set-up dialer connection: %v", err)
		return err
	}
	cleanup := func() error { return dialer.Close() }
	defer cleanup()

	dsn := fmt.Sprintf(
		"user=%s password=%s dbname=%s sslmode=disable",
		"postgres", pgPassword, pgDatabaseName,
	)

	config, err := pgxpool.ParseConfig(dsn)
	if err != nil {
		log.Warnf("failed to parse DSN config: %v", err)
		return err
	}

	pgInstanceURI := fmt.Sprintf("projects/%s/locations/%s/clusters/%s/instances/%s", projectID, region, pgClusterName, pgInstanceName)
	config.ConnConfig.DialFunc = func(ctx context.Context, _ string, _ string) (net.Conn, error) {
		return dialer.Dial(ctx, pgInstanceURI)
	}

	pool, err := pgxpool.NewWithConfig(context.Background(), config)
	if err != nil {
		log.Warnf("failed to set-up pgx pool: %v", err)
		return err
	}
	defer pool.Close()

	query := "SELECT id, name, description, picture, price_usd_currency_code, price_usd_units, price_usd_nanos, categories FROM " + pgTableName
	rows, err := pool.Query(context.Background(), query)
	if err != nil {
		log.Warnf("failed to query database: %v", err)
		return err
	}
	defer rows.Close()

	catalog.Products = catalog.Products[:0]
	for rows.Next() {
		product := &pb.Product{}
		product.PriceUsd = &pb.Money{}

		var categories string
		err = rows.Scan(&product.Id, &product.Name, &product.Description,
			&product.Picture, &product.PriceUsd.CurrencyCode, &product.PriceUsd.Units,
			&product.PriceUsd.Nanos, &categories)
		if err != nil {
			log.Warnf("failed to scan query result row: %v", err)
			return err
		}
		categories = strings.ToLower(categories)
		product.Categories = strings.Split(categories, ",")

		catalog.Products = append(catalog.Products, product)
	}

	log.Info("successfully parsed product catalog from AlloyDB")
	return nil
}
