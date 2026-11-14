package pipeline

import (
	"context"
	"fmt"
	"time"

	"contas/tools/ci/internal/runner"
)

type CheckOptions struct {
	SkipMigrations  bool
	CoverageFile    string
	TestPath        string
	DatabaseURL     string
	ContainerPrefix string
}

// RunCheck executes the full local validation pipeline: lint -> format-check -> migrations & tests.
func RunCheck(ctx context.Context, exec runner.CommandExecutor, projectDir string, opts CheckOptions) error {
	startTime := time.Now()
	fmt.Println("==========================================================")
	fmt.Println("🚀 [contas-ci] Starting Quality and Validation Pipeline")
	fmt.Println("==========================================================")

	// Step 1: Lint
	if err := RunLint(ctx, exec, projectDir); err != nil {
		return err
	}

	// Step 2: Format Check
	if err := RunFormatCheck(ctx, exec, projectDir, opts.ContainerPrefix); err != nil {
		return err
	}

	// Step 3: Tests with coverage
	testOpts := TestOptions{
		SkipMigrations: opts.SkipMigrations,
		CoverageFile:   opts.CoverageFile,
		TestPath:       opts.TestPath,
		DatabaseURL:    opts.DatabaseURL,
	}
	if err := RunTests(ctx, exec, projectDir, testOpts); err != nil {
		return err
	}

	fmt.Println("==========================================================")
	fmt.Printf("🎉 [contas-ci] Pipeline Check PASSED successfully in %s!\n", time.Since(startTime).Round(time.Millisecond))
	fmt.Println("==========================================================")
	return nil
}
