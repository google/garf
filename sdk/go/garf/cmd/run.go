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
	"strings"

	"github.com/google/garf/sdk/go/garf/garf"
	"github.com/spf13/cobra"
)

var runCmd = &cobra.Command{
	Use:   "run",
	Short: "Runs workflow from a file",
	Run: func(cmd *cobra.Command, args []string) {
		ctx := cmd.Context()
		var err error
		workflowPath, _ := cmd.Flags().GetString("file")
		configPath, _ := cmd.Flags().GetString("config")
		asFiles, _ := cmd.Flags().GetBool("as-file")
		enableCache, _ := cmd.Flags().GetBool("enable-cache")
		selectedAliases, _ := cmd.Flags().GetString("selected-aliases")
		excludedAliases, _ := cmd.Flags().GetString("excluded-aliases")
		var resultsFileWorkflow []string
		options := garf.WorkflowRequestOptions{}
		if enableCache {
			options.QueryRequestOptions.EnableCache = true
			options.QueryRequestOptions.CacheTtlSeconds = 60 * 60
		}
		if excludedAliases != "" {
			options.SkippedAliases = strings.Split(excludedAliases, ",")
		}
		if selectedAliases != "" {
			options.SelectedAliases = strings.Split(selectedAliases, ",")
		}
		if asFiles {
			options.QueryRequestOptions.ConfigPath = configPath
			resultsFileWorkflow, err = GarfClient.ExecuteWorkflowFromFile(ctx, workflowPath, &options)
			if err != nil {
				log.Fatalf("Failed to run the workflow: %v", err)
			}

		} else {
			config := &garf.Config{}
			if configPath != "" {
				config, err = garf.ReadConfigFromFile(configPath)
				if err != nil {
					log.Fatalf("Problem reading config: %v", err)
				}
			}
			workflow, err := garf.ReadWorkflowFromFile(workflowPath)
			if err != nil {
				log.Fatalf("Problem reading workflow: %v", err)
			}

			options.QueryRequestOptions.Config = config
			resultsFileWorkflow, err = GarfClient.ExecuteWorkflow(ctx, workflow, &options)
			if err != nil {
				log.Fatalf("Failed to run the workflow: %v", err)
			}
		}
		fmt.Println(resultsFileWorkflow)
	},
}

func init() {
	workflowCmd.AddCommand(runCmd)
	runCmd.Flags().StringP("file", "f", "", "Path to garf workflow")
	runCmd.Flags().StringP("config", "c", "", "Path to garf config")
	runCmd.Flags().Bool("as-file", false, "Whether to pass workflow/configs as file paths")
	runCmd.Flags().Bool("enable-cache", false, "Whether to enable caching on server")
	runCmd.Flags().StringP("selected-aliases", "i", "", "Workflow aliases to run")
	runCmd.Flags().StringP("skipped-aliases", "e", "", "Workflow aliases to exclude")
}
