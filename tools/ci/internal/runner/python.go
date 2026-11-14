package runner

import (
	"context"
	"fmt"
	"os"
	"path/filepath"
)

// ResolvePythonToolCommand returns the command and arguments to invoke a tool,
// checking for 'uv', virtualenv '.venv/bin/<tool>', or system binary.
func ResolvePythonToolCommand(projectDir, tool string, toolArgs ...string) (string, []string) {
	// 1. Check if uv is in PATH
	if _, err := NewDefaultExecutor().LookPath("uv"); err == nil {
		args := append([]string{"run", tool}, toolArgs...)
		return "uv", args
	}

	// 2. Check local virtualenv .venv/bin/<tool>
	venvTool := filepath.Join(projectDir, ".venv", "bin", tool)
	if _, err := os.Stat(venvTool); err == nil {
		return venvTool, toolArgs
	}

	// 3. Fallback to system tool
	return tool, toolArgs
}

// RunPythonTool runs a Python tool within the projectDir with proper resolution.
func RunPythonTool(ctx context.Context, exec CommandExecutor, projectDir, tool string, env map[string]string, args ...string) (*ExecutionResult, error) {
	cmd, resolvedArgs := ResolvePythonToolCommand(projectDir, tool, args...)
	opts := ExecutionOptions{
		Command:      cmd,
		Args:         resolvedArgs,
		WorkingDir:   projectDir,
		Env:          env,
		StreamOutput: true,
	}
	res, err := exec.Run(ctx, opts)
	if err != nil {
		return res, fmt.Errorf("%s failed: %w", tool, err)
	}
	return res, nil
}
