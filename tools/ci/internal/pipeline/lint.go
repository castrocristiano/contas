package pipeline

import (
	"context"
	"fmt"

	"contas/tools/ci/internal/runner"
)

// RunLint executes static analysis using Ruff.
func RunLint(ctx context.Context, exec runner.CommandExecutor, projectDir string) error {
	fmt.Println("🔍 [contas-ci] Running Ruff Linter (ruff check .)...")
	_, err := runner.RunPythonTool(ctx, exec, projectDir, "ruff", nil, "check", ".")
	if err != nil {
		return fmt.Errorf("linter check failed: %w", err)
	}
	fmt.Println("✅ [contas-ci] Linter checks passed successfully!")
	return nil
}
