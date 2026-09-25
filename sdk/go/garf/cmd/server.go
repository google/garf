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

	"github.com/spf13/cobra"
)

var serverCmd = &cobra.Command{
	Use:   "server",
	Short: "Server specific commands",
	Run: func(cmd *cobra.Command, args []string) {
		ctx := cmd.Context()
		info := GarfClient.GetInfo(ctx)
		fmt.Println(info)
	},
}

var versionCmd = &cobra.Command{
	Use:   "version",
	Short: "Show server version",
	Run: func(cmd *cobra.Command, args []string) {
		ctx := cmd.Context()
		version := GarfClient.GetVersion(ctx)
		fmt.Println(version)
	},
}

var infoCmd = &cobra.Command{
	Use:   "info",
	Short: "Show server info",
	Run: func(cmd *cobra.Command, args []string) {
		ctx := cmd.Context()
		info := GarfClient.GetInfo(ctx)
		fmt.Println(info)
	},
}

var fetchersCmd = &cobra.Command{
	Use:   "fetchers",
	Short: "Show available fetchers",
	Run: func(cmd *cobra.Command, args []string) {
		ctx := cmd.Context()
		fetchers := GarfClient.ListFetchers(ctx)
		fmt.Println(fetchers)
	},
}

var executorsCmd = &cobra.Command{
	Use:   "executors",
	Short: "Show available executors",
	Run: func(cmd *cobra.Command, args []string) {
		ctx := cmd.Context()
		executors := GarfClient.ListExecutors(ctx)
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
