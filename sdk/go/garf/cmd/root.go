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
	"os"
	"strings"

	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/trace"

	"github.com/google/garf/sdk/go/garf/garf"
	"github.com/spf13/cobra"
	"github.com/spf13/viper"
)

const name = "github.com/google/garf/sdk/go/garf"

var (
	tracer       = otel.Tracer(name)
	EnableCache  bool
	GarfEndpoint string
	GarfClient   *garf.Garf
)

var rootCmd = &cobra.Command{
	Use:     "garf",
	Short:   "Interact with garf",
	Version: "0.0.1",
	PersistentPreRunE: func(cmd *cobra.Command, args []string) error {
		ctx := context.Background()
		ctx, span := tracer.Start(ctx, "cli")
		cmd.SetContext(ctx)
		defer span.End()
		garfEndpoint := viper.GetString("endpoint")
		g := garf.New(ctx, garfEndpoint)
		GarfClient = g
		return nil
	},
	PersistentPostRunE: func(cmd *cobra.Command, args []string) error {
		if GarfClient != nil {
			GarfClient.Close()
		}
		if span := trace.SpanFromContext(cmd.Context()); span != nil {
			span.End()
		}
		return nil
	},
}

func Execute() {
	err := rootCmd.Execute()
	if err != nil {
		os.Exit(1)
	}
}

func init() {
	viper.AutomaticEnv()
	replacer := strings.NewReplacer("-", "_")
	rootCmd.PersistentFlags().StringVarP(&GarfEndpoint, "endpoint", "", "", "Garf server address")
	rootCmd.PersistentFlags().BoolVarP(&EnableCache, "enable-cache", "", false, "Whether to enable cache")
	viper.SetEnvKeyReplacer(replacer)
	viper.SetEnvPrefix("GARF")
	viper.BindPFlag("endpoint", rootCmd.PersistentFlags().Lookup("endpoint"))
	viper.BindPFlag("enable-cache", rootCmd.PersistentFlags().Lookup("enable-cache"))
}
