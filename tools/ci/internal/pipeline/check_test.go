package pipeline

import (
	"context"
	"fmt"
	"testing"

	"contas/tools/ci/internal/runner"
)

type mockExecutor struct {
	commandsRun []string
	shouldFail  bool
	failCommand string
}

func (m *mockExecutor) LookPath(file string) (string, error) {
	return "/mock/bin/" + file, nil
}

func (m *mockExecutor) Run(ctx context.Context, opts runner.ExecutionOptions) (*runner.ExecutionResult, error) {
	cmdStr := fmt.Sprintf("%s %v", opts.Command, opts.Args)
	m.commandsRun = append(m.commandsRun, cmdStr)

	if m.shouldFail && (m.failCommand == "" || opts.Command == m.failCommand) {
		return &runner.ExecutionResult{
			ExitCode: 1,
			Error:    fmt.Errorf("mock error for %s", opts.Command),
		}, fmt.Errorf("mock failure")
	}

	return &runner.ExecutionResult{
		ExitCode: 0,
		Stdout:   "mock stdout",
	}, nil
}

func TestRunCheck_Success(t *testing.T) {
	mock := &mockExecutor{}
	ctx := context.Background()

	opts := CheckOptions{
		SkipMigrations: true,
		CoverageFile:   "mock-coverage.xml",
	}

	err := RunCheck(ctx, mock, "/mock/project", opts)
	if err != nil {
		t.Fatalf("expected RunCheck to succeed, got: %v", err)
	}

	if len(mock.commandsRun) < 3 {
		t.Errorf("expected at least 3 commands to run, got %d: %v", len(mock.commandsRun), mock.commandsRun)
	}
}

func TestRunCheck_FailureOnLint(t *testing.T) {
	mock := &mockExecutor{
		shouldFail: true,
	}
	ctx := context.Background()

	opts := CheckOptions{
		SkipMigrations: true,
	}

	err := RunCheck(ctx, mock, "/mock/project", opts)
	if err == nil {
		t.Fatalf("expected RunCheck to fail when linter fails, got nil")
	}
}
