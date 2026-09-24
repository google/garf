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

	"github.com/google/garf/sdk/go/garf/garf"
	"github.com/spf13/cobra"
	"github.com/spf13/viper"
)

var serverCmd = &cobra.Command{
	Use:   "server",
	Short: "Show server info",
	Run: func(cmd *cobra.Command, args []string) {
		garfEndpoint := viper.GetString("endpoint")
		ctx := context.Background()
		g := garf.New(ctx, garfEndpoint)
		defer g.Close()
		info := g.GetInfo(ctx)
		fmt.Println(info)
	},
}

var versionCmd = &cobra.Command{
	Use:   "version",
	Short: "Show server version",
	Run: func(cmd *cobra.Command, args []string) {
		garfEndpoint := viper.GetString("endpoint")
		ctx := context.Background()
		g := garf.New(ctx, garfEndpoint)
		defer g.Close()
		version := g.GetVersion(ctx)
		fmt.Println(version)
	},
}

var infoCmd = &cobra.Command{
	Use:   "info",
	Short: "Show server info",
	Run: func(cmd *cobra.Command, args []string) {
		garfEndpoint := viper.GetString("endpoint")
		ctx := context.Background()
		g := garf.New(ctx, garfEndpoint)
		defer g.Close()
		info := g.GetInfo(ctx)
		fmt.Println(info)
	},
}

var fetchersCmd = &cobra.Command{
	Use:   "fetchers",
	Short: "Show available fetchers",
	Run: func(cmd *cobra.Command, args []string) {
		garfEndpoint := viper.GetString("endpoint")
		ctx := context.Background()
		g := garf.New(ctx, garfEndpoint)
		defer g.Close()
		fetchers := g.ListFetchers(ctx)
		fmt.Println(fetchers)
	},
}

var executorsCmd = &cobra.Command{
	Use:   "executors",
	Short: "Show available executors",
	Run: func(cmd *cobra.Command, args []string) {
		garfEndpoint := viper.GetString("endpoint")
		ctx := context.Background()
		g := garf.New(ctx, garfEndpoint)
		defer g.Close()
		executors := g.ListExecutors(ctx)
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
