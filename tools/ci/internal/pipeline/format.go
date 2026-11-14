package pipeline

import (
	"context"
	"fmt"
	"path/filepath"

	"contas/tools/ci/internal/runner"
)

// RunFormatCheck validates code formatting with Ruff and generates SonarQube formatter issue reports.
func RunFormatCheck(ctx context.Context, exec runner.CommandExecutor, projectDir string, containerPrefix string) error {
	fmt.Println("🎨 [contas-ci] Running Formatter Check (Ruff Format & SonarQube Reports)...")

	scriptPath := filepath.Join(projectDir, ".agents", "skills", "formatter", "scripts", "sonar_formatter_check.py")
	args := []string{scriptPath}
	if containerPrefix != "" {
		args = append(args, "--container-prefix", containerPrefix)
	}

	_, err := runner.RunPythonTool(ctx, exec, projectDir, "python3", nil, args...)
	if err != nil {
		return fmt.Errorf("formatter check failed (files unformatted or linter error): %w", err)
	}
	fmt.Println("✅ [contas-ci] Formatter check passed and Sonar reports generated!")
	return nil
}
