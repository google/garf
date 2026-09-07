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

// Package garf interacts with garf gRPC server.
package garf

import (
	"context"
	"log"

	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
	emptypb "google.golang.org/protobuf/types/known/emptypb"
	structpb "google.golang.org/protobuf/types/known/structpb"

	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/attribute"

	"go.opentelemetry.io/contrib/instrumentation/google.golang.org/grpc/otelgrpc"

	"go.opentelemetry.io/contrib/bridges/otelslog"
)

const name = "github.com/google/garf/sdk/go/garf"

var (
	tracer = otel.Tracer(name)
	logger = otelslog.NewLogger(name)
)

// Garf represents gRPC client to garf server.
type Garf struct {
	Endpoint string
}

// New creates new Garf instance.
func New(endpoint string) Garf {
	return Garf{Endpoint: endpoint}
}

func (g *Garf) init(ctx context.Context) (GarfServiceClient, *grpc.ClientConn) {
	ctx, span := tracer.Start(ctx, "init")
	defer span.End()
	conn, err := grpc.NewClient(
		g.Endpoint,
		grpc.WithTransportCredentials(insecure.NewCredentials()),
		grpc.WithStatsHandler(otelgrpc.NewClientHandler()),
	)
	if err != nil {
		log.Fatalf("did not connect: %v", err)
	}
	c := NewGarfServiceClient(conn)
	return c, conn
}

// GetVersion returns garf server version.
func (g *Garf) GetVersion() string {
	ctx, span := tracer.Start(context.Background(), "version")
	defer span.End()

	c, conn := g.init(ctx)
	defer conn.Close()

	r, err := c.GetVersion(ctx, &emptypb.Empty{})
	if err != nil {
		log.Fatalf("cannot get version: %v", err)
	}
	version := r.Version
	log.Printf("Version: %s", version)
	versionAttr := attribute.String("garf.version", version)
	span.SetAttributes(versionAttr)
	logger.InfoContext(ctx, "Getting version", "version", version)
	return r.Version
}

func (g *Garf) GetInfo() string {
	ctx, span := tracer.Start(context.Background(), "info")
	defer span.End()

	c, conn := g.init(ctx)
	defer conn.Close()

	r, err := c.GetInfo(ctx, &emptypb.Empty{})
	if err != nil {
		log.Fatalf("cannot get version: %v", err)
	}
	version := r.ExecutorsVersion
	log.Printf("Info: %s", r)
	span.SetAttributes(
		attribute.String("garf.io.version", r.IoVersion),
		attribute.String("garf.core.version", r.CoreVersion),
		attribute.String("garf.executors.version", r.ExecutorsVersion),
	)
	logger.InfoContext(ctx, "Getting info", "info", r)
	return version
}

func (g *Garf) ListFetchers() []string {
	ctx, span := tracer.Start(context.Background(), "list-fetchers")
	defer span.End()

	c, conn := g.init(ctx)
	defer conn.Close()

	r, err := c.ListFetchers(ctx, &emptypb.Empty{})
	if err != nil {
		log.Fatalf("cannot get fetchers: %v", err)
	}
	fetchers := r.Results
	log.Printf("Fetchers: %s", fetchers)
	var fetcherNames []string
	for _, fetcher := range fetchers {
		fetcherNames = append(fetcherNames, fetcher.Name)
	}
	fetchersAttr := attribute.StringSlice("garf.fetchers", fetcherNames)
	span.SetAttributes(fetchersAttr)
	logger.InfoContext(ctx, "Getting fetchers", "fetchers", fetcherNames)
	return fetcherNames
}

func (g *Garf) ListExecutors() []string {
	ctx, span := tracer.Start(context.Background(), "list-executors")
	defer span.End()

	c, conn := g.init(ctx)
	defer conn.Close()

	r, err := c.ListExecutors(ctx, &emptypb.Empty{})
	if err != nil {
		log.Fatalf("cannot get executors: %v", err)
	}
	executors := r.Results
	log.Printf("Executors: %s", executors)
	executorsAttr := attribute.StringSlice("garf.executors", executors)
	span.SetAttributes(executorsAttr)
	logger.InfoContext(ctx, "Getting executors", "executors", executors)
	return executors
}

func (g *Garf) Execute(title, query, writer string) []string {
	ctx, span := tracer.Start(context.Background(), "execute")
	defer span.End()

	c, conn := g.init(ctx)
	defer conn.Close()

	fetcherParameters := map[string]any{
		"n_rows": 10,
	}
	fetcherParameterStruct, err := structpb.NewStruct(fetcherParameters)
	if err != nil {
		log.Fatalf("Failed to create fetcher parameters: %v", err)
	}
	request := ExecuteRequest{
		Source: "fake",
		Title:  title,
		Query:  query,
		Context: &ExecutionContext{
			FetcherParameters: fetcherParameterStruct,
			Writer:            writer,
		},
	}
	span.SetAttributes(
		attribute.String("query.title", request.Title),
		attribute.String("query.text", request.Query),
		attribute.String("query.source", request.Source),
		attribute.String("query.context.writer", request.Context.Writer),
	)
	r, err := c.Execute(ctx, &request)
	if err != nil {
		logger.ErrorContext(ctx, "Failed query", "title", request.Title)
		log.Fatalf("cannot execute query: %v", err)
	}
	result := r.Results
	versionAttr := attribute.StringSlice("garf.results", result)
	span.SetAttributes(versionAttr)
	logger.InfoContext(ctx, "Executed query", "title", request.Title, "result", result)
	return result
}

func (g *Garf) ExecuteBatch(batch map[string]string, writer string) []string {
	ctx, span := tracer.Start(context.Background(), "execute-batch")
	defer span.End()

	c, conn := g.init(ctx)
	defer conn.Close()

	fetcherParameters := map[string]any{
		"n_rows": 10,
	}
	fetcherParameterStruct, err := structpb.NewStruct(fetcherParameters)
	if err != nil {
		log.Fatalf("Failed to create fetcher parameters: %v", err)
	}
	var queries []*QueryDefinition

	for title, query := range batch {
		queries = append(queries, &QueryDefinition{Title: title, Text: query})
	}
	request := ExecuteBatchRequest{
		Source: "fake",
		Batch:  queries,
		Context: &ExecutionContext{
			FetcherParameters: fetcherParameterStruct,
			Writer:            writer,
		},
	}
	span.SetAttributes(
		attribute.Int("query.batch_size", len(batch)),
		attribute.String("query.source", request.Source),
		attribute.String("query.context.writer", request.Context.Writer),
	)
	r, err := c.ExecuteBatch(ctx, &request)
	if err != nil {
		logger.ErrorContext(ctx, "Failed batch", "batch", queries)
		log.Fatalf("cannot execute batch: %v", queries)
	}
	result := r.Results
	versionAttr := attribute.StringSlice("garf.results", result)
	span.SetAttributes(versionAttr)
	logger.InfoContext(ctx, "Executed batch", "batch", queries, "result", result)
	return result
}
