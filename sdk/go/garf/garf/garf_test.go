package garf

import (
	"context"
	"testing"

	"github.com/google/garf/sdk/go/garf/internal/testenv"
)

var (
	g Garf
)

func TestGetVersion(t *testing.T) {
	ctx := context.Background()
	conn, _ := testenv.GetConnection()
	g := New(context.Background(), conn)
	version := g.GetVersion(ctx)
	if version != "1.7.0" {
		t.Errorf("Version mismatch, expected %s, got %s", "1.7.0", version)
	}
}

func TestGetInfo(t *testing.T) {
	ctx := context.Background()
	conn, _ := testenv.GetConnection()
	g := New(context.Background(), conn)
	version := g.GetInfo(ctx)
	if version != "1.7.0" {
		t.Errorf("Version mismatch, expected %s, got %s", "1.7.0", version)
	}
}
