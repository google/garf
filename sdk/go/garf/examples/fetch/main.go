package main

import (
	"context"
	"os"

	"github.com/jedib0t/go-pretty/v6/table"

	"github.com/google/garf/sdk/go/garf/garf"
)

func main() {

	garfEndpoint := os.Getenv("GARF_ENDPOINT")
	if garfEndpoint == "" {
		garfEndpoint = "127.0.0.1:50051"
	}
	g := garf.New(context.Background(), garfEndpoint)
	defer g.Close()
	fetchQueryInline(g)
}

func fetchQueryInline(g *garf.Garf) error {
	results := g.Fetch("test",
		"SELECT metric.int AS field, metric.float AS field2 FROM fake",
	)
	t := table.NewWriter()
	t.SetOutputMirror(os.Stdout)
	columns := results.Columns
	headerRow := make(table.Row, len(columns))
	for i, c := range columns {
		headerRow[i] = c
	}
	t.AppendHeader(headerRow)
	for _, v := range results.Rows {
		row := make(table.Row, len(v.Fields))
		rowMap := v.AsMap()
		for i, c := range columns {
			row[i] = rowMap[c]
		}
		t.AppendRow(row)
	}
	t.Render()
	return nil
}
