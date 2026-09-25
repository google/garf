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
	Args:  cobra.ExactArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		ctx := cmd.Context()
		writer, _ := cmd.Flags().GetString("writer")
		source, _ := cmd.Flags().GetString("source")
		queryAsFile, _ := cmd.Flags().GetBool("as-file")
		var results []string
		if queryAsFile {
			results = GarfClient.ExecuteFromFile(ctx, source, args[0], writer)
		} else {
			p := filepath.Clean(args[0])
			queryData, err := os.ReadFile(args[0])
			if err != nil {
				log.Fatal("File not found")
			}
			ext := filepath.Ext(p)
			title := strings.TrimSuffix(filepath.Base(p), ext)
			results = GarfClient.Execute(ctx, source, title, string(queryData), writer)
		}
		fmt.Println(results)
	},
}

func init() {
	rootCmd.AddCommand(executeCmd)
	executeCmd.Flags().StringP("source", "s", "fake", "Type of API source")
	executeCmd.Flags().StringP("writer", "w", "json", "Name of writer")
	executeCmd.Flags().Bool("as-file", false, "Whether to pass query as a file path")
}
