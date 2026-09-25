package main

import (
	"context"
	"fmt"
	"os"

	"github.com/google/garf/sdk/go/garf/garf"
)

func main() {

	ctx := context.Background()
	garfEndpoint := os.Getenv("GARF_ENDPOINT")
	if garfEndpoint == "" {
		garfEndpoint = "127.0.0.1:50051"
	}
	g := garf.New(ctx, garfEndpoint)
	defer g.Close()
	runHelperFunctions(ctx, g)
}

func runHelperFunctions(ctx context.Context, g *garf.Garf) {
	version := g.GetVersion(ctx)
	fmt.Println(version)

	info := g.GetInfo(ctx)
	fmt.Println(info)

	fetchers := g.ListFetchers(ctx)
	fmt.Println(fetchers)

	executors := g.ListExecutors(ctx)
	fmt.Println(executors)
}
