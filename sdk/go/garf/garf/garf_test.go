package garf

import (
	"context"
	"testing"

	"github.com/google/garf/sdk/go/internal/testenv"
)

var (
	g Garf
)

func TestGetVersion(t *testing.T) {
	conn, _ := testenv.GetConnection()
	g := New(context.Background(), conn)
	version := g.GetVersion()
	if version != "1.7.0" {
		t.Errorf("Version mismatch, expected %s, got %s", "1.7.0", version)
	}
}

func TestGetInfo(t *testing.T) {
	conn, _ := testenv.GetConnection()
	g := New(context.Background(), conn)
	version := g.GetInfo()
	if version != "1.7.0" {
		t.Errorf("Version mismatch, expected %s, got %s", "1.7.0", version)
	}
}
