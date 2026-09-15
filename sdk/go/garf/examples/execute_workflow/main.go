package main

import (
	"context"
	"fmt"
	"log"
	"os"

	"github.com/google/garf/sdk/go/garf/garf"
	structpb "google.golang.org/protobuf/types/known/structpb"
)

func main() {

	garfEndpoint := os.Getenv("GARF_ENDPOINT")
	if garfEndpoint == "" {
		garfEndpoint = "127.0.0.1:50051"
	}
	g := garf.New(context.Background(), garfEndpoint)
	defer g.Close()
	runInlineWorkflow(g)
	runWorkflowFromFile(g)
}

func runWorkflowFromFile(g *garf.Garf) error {
	workflow, err := garf.ReadWorkflowFromFile("test_workflow.yaml")
	if err != nil {
		log.Fatalf("Failed to parse workflow: %v", err)
	}

	resultsFileWorkflow := g.ExecuteWorkflow(workflow, &garf.Config{}, &garf.ExecutionContext{})
	fmt.Println(resultsFileWorkflow)
	return err

}
func runInlineWorkflow(g *garf.Garf) error {
	fetcherParameters := map[string]any{
		"n_rows": 10,
	}
	fetcherParameterStruct, _ := structpb.NewStruct(fetcherParameters)

	globalFetcherParameters := map[string]any{
		"n_rows": 5,
	}
	globalFetcherParametersStruct, _ := structpb.NewStruct(globalFetcherParameters)
	sourcesParameters := map[string]any{
		"fake": map[string]any{
			"fetcher_parameters": map[string]any{"n_rows": 1},
		},
	}
	sourcesStruct, _ := structpb.NewStruct(sourcesParameters)

	workflow := garf.Workflow{
		Name: "test",
		Steps: []*garf.WorkflowStep{
			{
				Fetcher: "fake",
				Alias:   "test",
				Writer:  "json",
				Queries: []*garf.QueryEntry{
					{
						Query: &garf.QueryDefinition{
							Title: "test_workflow",
							Text:  "SELECT metric.int AS field FROM fake",
						},
					},
				},
				FetcherParameters: fetcherParameterStruct,
			},
		},
	}
	config := garf.Config{
		Name: "test-config",
		GlobalParameters: &garf.ExecutionContext{
			FetcherParameters: globalFetcherParametersStruct,
		},
		Sources: sourcesStruct,
	}
	contextStruct, _ := structpb.NewStruct(map[string]any{
		"n_rows": 20,
	})

	executionContext := garf.ExecutionContext{
		FetcherParameters: contextStruct,
	}
	resultsWorkflow := g.ExecuteWorkflow(&workflow, &config, &executionContext)
	fmt.Println(resultsWorkflow)
	return nil

}
