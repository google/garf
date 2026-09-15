package main

import (
	"os"
	"testing"

	"github.com/google/garf/sdk/go/garf/internal/testenv"
)

func TestMain(m *testing.M) {
	exitCode := m.Run()
	testenv.Teardown()
	os.Exit(exitCode)
}
