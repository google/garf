package main

import (
	"context"
	"fmt"
	"log"
	"os"
	"path/filepath"
	"runtime"

	"github.com/google/garf/sdk/go/garf/garf"
)

func main() {

	garfEndpoint := os.Getenv("GARF_ENDPOINT")
	if garfEndpoint == "" {
		garfEndpoint = "127.0.0.1:50051"
	}
	g := garf.New(context.Background(), garfEndpoint)
	defer g.Close()
	executeQueryBatchInline(g)
	executeQueryBatchFromFiles(g)
}

func executeQueryBatchInline(g *garf.Garf) error {
	ctx := context.Background()
	batch := map[string]string{
		"test":  "SELECT metric.int AS field FROM fake",
		"test2": "SELECT metric.int AS field FROM fake",
		"test3": "SELECT metric.int AS field FROM fake",
	}
	resultsBatch, err := g.ExecuteBatch(ctx, "fake", batch, "json")
	if err != nil {
		log.Fatalf("Failed to execute batch: %v", err)
	}
	fmt.Println(resultsBatch)
	return nil
}

func executeQueryBatchFromFiles(g *garf.Garf) error {
	_, filename, _, _ := runtime.Caller(0)
	exeDir := filepath.Dir(filename)
	ctx := context.Background()
	batch := []string{
		filepath.Join(exeDir, "query1.sql"),
		filepath.Join(exeDir, "query2.sql"),
	}
	resultsBatch, err := g.ExecuteBatchFromFiles(ctx, "fake", batch, "json")
	if err != nil {
		log.Fatalf("Failed to execute batch: %v", err)
	}
	fmt.Println(resultsBatch)
	return nil
}
