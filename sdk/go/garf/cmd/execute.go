// Copyright 2026 Google LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     https://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

package cmd

import (
	"context"
	"fmt"
	"log"
	"os"
	"path/filepath"
	"strings"

	"github.com/spf13/cobra"
)

var executeCmd = &cobra.Command{
	Use:   "execute",
	Short: "Executes queries",
	Args:  cobra.MinimumNArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		ctx := cmd.Context()
		writer, _ := cmd.Flags().GetString("writer")
		source, _ := cmd.Flags().GetString("source")
		queryAsFile, _ := cmd.Flags().GetBool("as-file")
		var results []string
		if len(args) > 1 {
			results = runQueryBatch(ctx, source, args, writer, queryAsFile)
		} else {
			results = runQuery(ctx, source, args[0], writer, queryAsFile)
		}
		fmt.Println(results)
	},
}

func runQueryBatch(ctx context.Context, source string, batch []string, writer string, queryAsFile bool) []string {
	var err error
	var results []string
	if queryAsFile {
		results, err = GarfClient.ExecuteBatchFromFiles(ctx, source, batch, writer)
		if err != nil {
			log.Fatalf("Failed to run batch: %v", err)
		}
	} else {
		batchQueries := make(map[string]string)
		for _, query := range batch {
			p := filepath.Clean(query)
			queryData, err := os.ReadFile(query)
			if err != nil {
				log.Fatal("File not found")
			}
			ext := filepath.Ext(p)
			title := strings.TrimSuffix(filepath.Base(p), ext)
			batchQueries[title] = string(queryData)
			results, err = GarfClient.ExecuteBatch(ctx, source, batchQueries, writer)
			if err != nil {
				log.Fatalf("Failed to run batch: %v", err)
			}
		}
	}
	return results
}

func runQuery(ctx context.Context, source, query, writer string, queryAsFile bool) []string {
	var err error
	var results []string
	if queryAsFile {
		results, err = GarfClient.ExecuteFromFile(ctx, source, query, writer)
		if err != nil {
			log.Fatalf("Failed to run batch: %v", err)
		}
	} else {
		p := filepath.Clean(query)
		queryData, err := os.ReadFile(query)
		if err != nil {
			log.Fatal("File not found")
		}
		ext := filepath.Ext(p)
		title := strings.TrimSuffix(filepath.Base(p), ext)
		results, err = GarfClient.Execute(ctx, source, title, string(queryData), writer)
		if err != nil {
			log.Fatalf("Failed to run batch: %v", err)
		}
	}
	return results
}

func init() {
	rootCmd.AddCommand(executeCmd)
	executeCmd.Flags().StringP("source", "s", "fake", "Type of API source")
	executeCmd.Flags().StringP("writer", "w", "json", "Name of writer")
	executeCmd.Flags().Bool("as-file", false, "Whether to pass query as a file path")
}
