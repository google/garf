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
	runHelperFunctions(g)
}

func runHelperFunctions(g *garf.Garf) {
	version := g.GetVersion()
	fmt.Println(version)

	info := g.GetInfo()
	fmt.Println(info)

	fetchers := g.ListFetchers()
	fmt.Println(fetchers)

	executors := g.ListExecutors()
	fmt.Println(executors)
}
