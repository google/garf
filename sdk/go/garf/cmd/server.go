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

	"github.com/spf13/cobra"
)

var serverCmd = &cobra.Command{
	Use:   "server",
	Short: "Server specific commands",
	Run: func(cmd *cobra.Command, args []string) {
		ctx := cmd.Context()
		info, err := GarfClient.GetInfo(ctx)
		if err != nil {
			log.Fatalf("Failed to get version: %v", err)
		}
		fmt.Println(info)
	},
}

var versionCmd = &cobra.Command{
	Use:   "version",
	Short: "Show server version",
	Run: func(cmd *cobra.Command, args []string) {
		ctx := cmd.Context()
		version, err := GarfClient.GetVersion(ctx)
		if err != nil {
			log.Fatalf("Failed to get version: %v", err)
		}
		fmt.Println(version)
	},
}

var infoCmd = &cobra.Command{
	Use:   "info",
	Short: "Show server info",
	Run: func(cmd *cobra.Command, args []string) {
		ctx := cmd.Context()
		info, err := GarfClient.GetInfo(ctx)
		if err != nil {
			log.Fatalf("Failed to get info: %v", err)
		}
		fmt.Println(info)
	},
}

var fetchersCmd = &cobra.Command{
	Use:   "fetchers",
	Short: "Show available fetchers",
	Run: func(cmd *cobra.Command, args []string) {
		ctx := cmd.Context()
		fetchers, err := GarfClient.ListFetchers(ctx)
		if err != nil {
			log.Fatalf("Failed to get fetchers: %v", err)
		}
		fmt.Println(fetchers)
	},
}

var executorsCmd = &cobra.Command{
	Use:   "executors",
	Short: "Show available executors",
	Run: func(cmd *cobra.Command, args []string) {
		ctx := cmd.Context()
		executors, err := GarfClient.ListExecutors(ctx)
		if err != nil {
			log.Fatalf("Failed to get executors: %v", err)
		}
		fmt.Println(executors)
	},
}

func init() {
	rootCmd.AddCommand(serverCmd)
	serverCmd.AddCommand(versionCmd)
	serverCmd.AddCommand(infoCmd)
	serverCmd.AddCommand(fetchersCmd)
	serverCmd.AddCommand(executorsCmd)
}
