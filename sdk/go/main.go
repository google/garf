// Copyright 2026 Google LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//	https://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
package main

import (
	"context"
	"errors"
	"fmt"
	"log"
	"os"

	"buf.build/go/protoyaml"
	"github.com/google/garf/sdk/go/garf"
	"github.com/google/garf/sdk/go/telemetry"
	structpb "google.golang.org/protobuf/types/known/structpb"
)

func run() (error error) {
	ctx := context.Background()
	otelShutdown, err := telemetry.SetupOtelSdk(ctx)
	if err != nil {
		return err
	}

	defer func() {
		err = errors.Join(err, otelShutdown(context.Background()))
	}()
	garfEndpoint := os.Getenv("GARF_ENDPOINT")
	if garfEndpoint == "" {
		garfEndpoint = "127.0.0.1:50051"
	}
	g := garf.New(garfEndpoint)

	runHelperFunctions(g)
	executeQueryInline(g)
	executeQueryFromFile(g)
	executeQueryBatchInline(g)
	runInlineWorkflow(g)
	runWorkflowFromFile(g)

	return nil
}

func runHelperFunctions(g garf.Garf) {
	version := g.GetVersion()
	fmt.Println(version)

	info := g.GetInfo()
	fmt.Println(info)

	fetchers := g.ListFetchers()
	fmt.Println(fetchers)

	executors := g.ListExecutors()
	fmt.Println(executors)
}

func executeQueryInline(g garf.Garf) error {
	results := g.Execute("test", "SELECT metric.int AS field FROM fake", "json")
	fmt.Println(results)
	return nil
}

func executeQueryFromFile(g garf.Garf) error {
	queryData, err := os.ReadFile("../../libs/executors/tests/unit/workflows/test_query.sql")
	results := g.Execute("test", string(queryData), "json")
	fmt.Println(results)
	return err
}

func executeQueryBatchInline(g garf.Garf) error {
	batch := map[string]string{
		"test":  "SELECT metric.int AS field FROM fake",
		"test2": "SELECT metric.int AS field FROM fake",
		"test3": "SELECT metric.int AS field FROM fake",
	}
	resultsBatch := g.ExecuteBatch(batch, "json")
	fmt.Println(resultsBatch)
	return nil
}

func runWorkflowFromFile(g garf.Garf) error {
	workflowData, err := os.ReadFile("../../libs/executors/tests/unit/workflows/test_workflow.yaml")
	var workflowFile garf.Workflow
	options := protoyaml.UnmarshalOptions{
		AllowPartial: true,
		DiscardUnknown: true,

	}
	if err := options.Unmarshal(workflowData, &workflowFile); err != nil {
		log.Fatalf("Failed to parse workflow: %v", err)
	}

	resultsFileWorkflow := g.ExecuteWorkflow(&workflowFile, &garf.Config{}, &garf.ExecutionContext{})
	fmt.Println(resultsFileWorkflow)
	return err

}
func runInlineWorkflow(g garf.Garf) error {
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

func main() {
	if err := run(); err != nil {
		log.Fatalln(err)
	}
}
