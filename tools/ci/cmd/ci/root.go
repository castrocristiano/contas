package main

import (
	"fmt"
	"os"
	"path/filepath"

	"github.com/spf13/cobra"
)

var (
	verboseFlag bool
	dirFlag     string
)

var rootCmd = &cobra.Command{
	Use:   "contas-ci",
	Short: "Unified CI/CD validation and quality pipeline runner for Contas",
	Long: `contas-ci is the unified CI/CD runner for the Contas project.
It consolidates linting, formatting checks, database migrations, tests with coverage,
and full SonarQube Quality Gate analysis into a single compiled Go CLI.`,
}

func init() {
	rootCmd.PersistentFlags().BoolVarP(&verboseFlag, "verbose", "v", false, "enable detailed verbose logging")
	rootCmd.PersistentFlags().StringVar(&dirFlag, "dir", "", "project root directory (defaults to current working directory)")
}

func resolveProjectDir() (string, error) {
	if dirFlag != "" {
		abs, err := filepath.Abs(dirFlag)
		if err != nil {
			return "", fmt.Errorf("invalid directory '%s': %w", dirFlag, err)
		}
		return abs, nil
	}

	cwd, err := os.Getwd()
	if err != nil {
		return "", fmt.Errorf("unable to determine current working directory: %w", err)
	}

	// If running from tools/ci, ascend to root if .git or pyproject.toml is found
	current := cwd
	for {
		if _, err := os.Stat(filepath.Join(current, "pyproject.toml")); err == nil {
			return current, nil
		}
		parent := filepath.Dir(current)
		if parent == current {
			break
		}
		current = parent
	}

	return cwd, nil
}
