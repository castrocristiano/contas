package pipeline

import (
	"context"
	"fmt"
	"os"

	"contas/tools/ci/internal/runner"
)

type TestOptions struct {
	SkipMigrations bool
	CoverageFile   string
	TestPath       string
	DatabaseURL    string
}

// RunTests executes database migrations and pytest with code coverage generation.
func RunTests(ctx context.Context, exec runner.CommandExecutor, projectDir string, opts TestOptions) error {
	env := make(map[string]string)
	if opts.DatabaseURL != "" {
		env["DATABASE_URL"] = opts.DatabaseURL
	} else if dbEnv := os.Getenv("DATABASE_URL"); dbEnv != "" {
		env["DATABASE_URL"] = dbEnv
	}

	coverageFile := opts.CoverageFile
	if coverageFile == "" {
		coverageFile = "coverage.xml"
	}

	testPath := opts.TestPath
	if testPath == "" {
		testPath = "tests/unit/"
	}

	// 1. Database migrations (alembic upgrade head)
	if !opts.SkipMigrations {
		fmt.Println("📦 [contas-ci] Running Database Migrations (alembic upgrade head)...")
		_, err := runner.RunPythonTool(ctx, exec, projectDir, "alembic", env, "upgrade", "head")
		if err != nil {
			fmt.Printf("⚠️  [contas-ci] Alembic migration warning: %v (continuing to unit tests)\n", err)
		} else {
			fmt.Println("✅ [contas-ci] Migrations applied successfully!")
		}
	}

	// 2. Unit and Integration tests with coverage
	fmt.Printf("🧪 [contas-ci] Running Tests (%s) with coverage (%s)...\n", testPath, coverageFile)
	pytestArgs := []string{
		"-v",
		testPath,
		"--cov=src/contas",
		fmt.Sprintf("--cov-report=xml:%s", coverageFile),
	}

	_, err := runner.RunPythonTool(ctx, exec, projectDir, "pytest", env, pytestArgs...)
	if err != nil {
		return fmt.Errorf("tests failed: %w", err)
	}

	fmt.Println("✅ [contas-ci] All tests completed with coverage report generated!")
	return nil
}
