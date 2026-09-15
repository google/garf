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

	"github.com/google/garf/sdk/go/garf"
	"github.com/spf13/cobra"
	"github.com/spf13/viper"
)

var executeCmd = &cobra.Command{
	Use:   "execute",
	Short: "Executes queries",
	Args:  cobra.ExactArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		garfEndpoint := viper.GetString("endpoint")
		g := garf.New(context.Background(), garfEndpoint)
		defer g.Close()
		p := filepath.Clean(args[0])
		queryData, err := os.ReadFile(args[0])
		if err != nil {
			log.Fatal("File not found")
		}
		ext := filepath.Ext(p)
		title := strings.TrimSuffix(filepath.Base(p), ext)
		writer, _ := cmd.Flags().GetString("writer")
		source, _ := cmd.Flags().GetString("source")
		results := g.Execute(source, title, string(queryData), writer)
		fmt.Println(results)
	},
}

func init() {
	rootCmd.AddCommand(executeCmd)
	executeCmd.Flags().StringP("source", "s", "fake", "Type of API source")
	executeCmd.Flags().StringP("writer", "w", "json", "Name of writer")
}
