package runner

import (
	"bytes"
	"context"
	"fmt"
	"io"
	"os"
	"os/exec"
	"strings"
	"time"
)

// ExecutionOptions defines configuration for running an external process.
type ExecutionOptions struct {
	Command      string
	Args         []string
	Env          map[string]string
	WorkingDir   string
	Timeout      time.Duration
	StreamOutput bool
	Stdout       io.Writer
	Stderr       io.Writer
}

// ExecutionResult captures the output and exit status of a command run.
type ExecutionResult struct {
	ExitCode int
	Duration time.Duration
	Stdout   string
	Stderr   string
	Error    error
}

// CommandExecutor abstracts process execution for easy mocking in unit tests.
type CommandExecutor interface {
	Run(ctx context.Context, opts ExecutionOptions) (*ExecutionResult, error)
	LookPath(file string) (string, error)
}

// DefaultExecutor implements CommandExecutor using os/exec.
type DefaultExecutor struct{}

func NewDefaultExecutor() *DefaultExecutor {
	return &DefaultExecutor{}
}

func (e *DefaultExecutor) LookPath(file string) (string, error) {
	return exec.LookPath(file)
}

// Run executes a command with the provided options, streaming and capturing outputs.
func (e *DefaultExecutor) Run(ctx context.Context, opts ExecutionOptions) (*ExecutionResult, error) {
	if opts.Timeout > 0 {
		var cancel context.CancelFunc
		ctx, cancel = context.WithTimeout(ctx, opts.Timeout)
		defer cancel()
	}

	cmd := exec.CommandContext(ctx, opts.Command, opts.Args...)
	if opts.WorkingDir != "" {
		cmd.Dir = opts.WorkingDir
	}

	// Setup environment
	cmd.Env = os.Environ()
	for k, v := range opts.Env {
		cmd.Env = append(cmd.Env, fmt.Sprintf("%s=%s", k, v))
	}

	var stdoutBuf, stderrBuf bytes.Buffer

	// Configure stdout
	if opts.StreamOutput {
		if opts.Stdout != nil {
			cmd.Stdout = io.MultiWriter(opts.Stdout, &stdoutBuf)
		} else {
			cmd.Stdout = io.MultiWriter(os.Stdout, &stdoutBuf)
		}
	} else {
		if opts.Stdout != nil {
			cmd.Stdout = io.MultiWriter(opts.Stdout, &stdoutBuf)
		} else {
			cmd.Stdout = &stdoutBuf
		}
	}

	// Configure stderr
	if opts.StreamOutput {
		if opts.Stderr != nil {
			cmd.Stderr = io.MultiWriter(opts.Stderr, &stderrBuf)
		} else {
			cmd.Stderr = io.MultiWriter(os.Stderr, &stderrBuf)
		}
	} else {
		if opts.Stderr != nil {
			cmd.Stderr = io.MultiWriter(opts.Stderr, &stderrBuf)
		} else {
			cmd.Stderr = &stderrBuf
		}
	}

	startTime := time.Now()
	err := cmd.Run()
	duration := time.Since(startTime)

	result := &ExecutionResult{
		Duration: duration,
		Stdout:   strings.TrimSpace(stdoutBuf.String()),
		Stderr:   strings.TrimSpace(stderrBuf.String()),
	}

	if err != nil {
		result.Error = err
		if exitErr, ok := err.(*exec.ExitError); ok {
			result.ExitCode = exitErr.ExitCode()
		} else {
			result.ExitCode = 1
		}
		return result, fmt.Errorf("command '%s %s' failed (exit %d): %w", opts.Command, strings.Join(opts.Args, " "), result.ExitCode, err)
	}

	result.ExitCode = 0
	return result, nil
}
