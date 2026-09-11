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

	version := g.GetVersion()
	fmt.Println(version)

	info := g.GetInfo()
	fmt.Println(info)

	fetchers := g.ListFetchers()
	fmt.Println(fetchers)

	executors := g.ListExecutors()
	fmt.Println(executors)

	results := g.Execute("test", "SELECT metric.int AS field FROM fake", "json")
	fmt.Println(results)

	batch := map[string]string{
		"test":  "SELECT metric.int AS field FROM fake",
		"test2": "SELECT metric.int AS field FROM fake",
		"test3": "SELECT metric.int AS field FROM fake",
	}
	resultsBatch := g.ExecuteBatch(batch, "json")
	fmt.Println(resultsBatch)

	fetcherParameters := map[string]any{
		"n_rows": 10,
	}
	fetcherParameterStruct, err := structpb.NewStruct(fetcherParameters)

	globalFetcherParameters := map[string]any{
		"n_rows": 5,
	}
	globalFetcherParametersStruct, err := structpb.NewStruct(globalFetcherParameters)
	sourcesParameters := map[string]any{
		"fake": map[string]any{
			"fetcher_parameters": map[string]any{"n_rows": 1},
		},
	}
	sourcesStruct, err := structpb.NewStruct(sourcesParameters)

	workflow := garf.Workflow{
		Name: "test",
		Steps: []*garf.WorkflowStep{
			{
				Fetcher: "fake",
				Alias:   "test",
				Writer:  "json",
				Queries: []*garf.QueryDefinition{
					{
						Title: "test_workflow",
						Text:  "SELECT metric.int AS field FROM fake",
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
	contextStruct, err := structpb.NewStruct(map[string]any{
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
