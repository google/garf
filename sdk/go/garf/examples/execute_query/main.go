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
	ctx := context.Background()
	g := garf.New(ctx, garfEndpoint)
	defer g.Close()
	executeQueryInline(g)
	executeQueryFromFile(g)
}

func executeQueryInline(g *garf.Garf) error {
	ctx := context.Background()
	results := g.Execute(ctx, "fake", "test", "SELECT metric.int AS field FROM fake", "json")
	fmt.Println(results)
	return nil
}

func executeQueryFromFile(g *garf.Garf) error {
	ctx := context.Background()
	queryData, err := os.ReadFile("test_query.sql")
	results := g.Execute(ctx, "fake", "test", string(queryData), "json")
	fmt.Println(results)
	return err
}
