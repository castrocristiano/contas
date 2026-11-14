package runner

import (
	"context"
	"strings"
	"testing"
	"time"
)

func TestDefaultExecutor_Run_Success(t *testing.T) {
	executor := NewDefaultExecutor()
	ctx := context.Background()

	opts := ExecutionOptions{
		Command: "echo",
		Args:    []string{"hello", "world"},
	}

	res, err := executor.Run(ctx, opts)
	if err != nil {
		t.Fatalf("expected command to succeed, got: %v", err)
	}

	if res.ExitCode != 0 {
		t.Errorf("expected exit code 0, got %d", res.ExitCode)
	}

	if res.Stdout != "hello world" {
		t.Errorf("expected stdout 'hello world', got '%s'", res.Stdout)
	}
}

func TestDefaultExecutor_Run_Failure(t *testing.T) {
	executor := NewDefaultExecutor()
	ctx := context.Background()

	opts := ExecutionOptions{
		Command: "sh",
		Args:    []string{"-c", "exit 42"},
	}

	res, err := executor.Run(ctx, opts)
	if err == nil {
		t.Fatalf("expected error from failing command, got nil")
	}

	if res.ExitCode != 42 {
		t.Errorf("expected exit code 42, got %d", res.ExitCode)
	}
}

func TestDefaultExecutor_Run_Timeout(t *testing.T) {
	executor := NewDefaultExecutor()
	ctx := context.Background()

	opts := ExecutionOptions{
		Command: "sleep",
		Args:    []string{"2"},
		Timeout: 50 * time.Millisecond,
	}

	_, err := executor.Run(ctx, opts)
	if err == nil {
		t.Fatalf("expected timeout error, got nil")
	}

	if !strings.Contains(err.Error(), "signal: killed") && !strings.Contains(err.Error(), "context deadline exceeded") {
		t.Logf("command timed out as expected with error: %v", err)
	}
}
