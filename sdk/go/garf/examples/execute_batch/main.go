package main

import (
	"context"
	"fmt"
	"os"

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
}

func executeQueryBatchInline(g *garf.Garf) error {
	ctx := context.Background()
	batch := map[string]string{
		"test":  "SELECT metric.int AS field FROM fake",
		"test2": "SELECT metric.int AS field FROM fake",
		"test3": "SELECT metric.int AS field FROM fake",
	}
	resultsBatch := g.ExecuteBatch(ctx, batch, "json")
	fmt.Println(resultsBatch)
	return nil
}
