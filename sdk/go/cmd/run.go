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

	"github.com/google/garf/sdk/go/garf"
	"github.com/spf13/cobra"
	"github.com/spf13/viper"
)

var runCmd = &cobra.Command{
	Use:   "run",
	Short: "Runs workflow from a file",
	Run: func(cmd *cobra.Command, args []string) {
		garfEndpoint := viper.GetString("endpoint")
		g := garf.New(garfEndpoint)
		var err error
		workflowPath, _ := cmd.Flags().GetString("file")
		configPath, _ := cmd.Flags().GetString("config")
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

		resultsFileWorkflow := g.ExecuteWorkflow(workflow, config, &garf.ExecutionContext{})
		fmt.Println(resultsFileWorkflow)
	},
}

func init() {
	workflowCmd.AddCommand(runCmd)
	runCmd.Flags().StringP("file", "f", "", "Path to garf workflow")
	runCmd.Flags().StringP("config", "c", "", "Path to garf config")
}
