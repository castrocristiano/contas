package main

import (
	"context"
	"fmt"
	"os"

	"github.com/spf13/cobra"

	"contas/tools/ci/internal/pipeline"
	"contas/tools/ci/internal/runner"
)

var (
	skipMigrationsFlag bool
	coverageFileFlag   string
	testPathFlag       string
	containerPrefix    string
)

var checkCmd = &cobra.Command{
	Use:   "check",
	Short: "Run full local validation pipeline (lint, format-check, test with coverage)",
	RunE: func(cmd *cobra.Command, args []string) error {
		dir, err := resolveProjectDir()
		if err != nil {
			return err
		}
		opts := pipeline.CheckOptions{
			SkipMigrations:  skipMigrationsFlag,
			CoverageFile:    coverageFileFlag,
			TestPath:        testPathFlag,
			ContainerPrefix: containerPrefix,
		}
		exec := runner.NewDefaultExecutor()
		return pipeline.RunCheck(context.Background(), exec, dir, opts)
	},
}

var lintCmd = &cobra.Command{
	Use:   "lint",
	Short: "Run static code analysis with Ruff (ruff check .)",
	RunE: func(cmd *cobra.Command, args []string) error {
		dir, err := resolveProjectDir()
		if err != nil {
			return err
		}
		exec := runner.NewDefaultExecutor()
		return pipeline.RunLint(context.Background(), exec, dir)
	},
}

var formatCheckCmd = &cobra.Command{
	Use:   "format-check",
	Short: "Validate code formatting and generate SonarQube reports",
	RunE: func(cmd *cobra.Command, args []string) error {
		dir, err := resolveProjectDir()
		if err != nil {
			return err
		}
		exec := runner.NewDefaultExecutor()
		return pipeline.RunFormatCheck(context.Background(), exec, dir, containerPrefix)
	},
}

var testCmd = &cobra.Command{
	Use:   "test",
	Short: "Run database migrations and unit/integration tests with coverage",
	RunE: func(cmd *cobra.Command, args []string) error {
		dir, err := resolveProjectDir()
		if err != nil {
			return err
		}
		opts := pipeline.TestOptions{
			SkipMigrations: skipMigrationsFlag,
			CoverageFile:   coverageFileFlag,
			TestPath:       testPathFlag,
		}
		exec := runner.NewDefaultExecutor()
		return pipeline.RunTests(context.Background(), exec, dir, opts)
	},
}

func init() {
	checkCmd.Flags().BoolVar(&skipMigrationsFlag, "skip-migrations", false, "skip running database migrations before tests")
	checkCmd.Flags().StringVar(&coverageFileFlag, "coverage-file", "coverage.xml", "coverage XML output file path")
	checkCmd.Flags().StringVar(&testPathFlag, "test-path", "tests/unit/", "target test path or pattern")
	checkCmd.Flags().StringVar(&containerPrefix, "container-prefix", "", "container prefix path for coverage files (e.g. /usr/src)")

	testCmd.Flags().BoolVar(&skipMigrationsFlag, "skip-migrations", false, "skip running database migrations before tests")
	testCmd.Flags().StringVar(&coverageFileFlag, "coverage-file", "coverage.xml", "coverage XML output file path")
	testCmd.Flags().StringVar(&testPathFlag, "test-path", "tests/unit/", "target test path or pattern")

	formatCheckCmd.Flags().StringVar(&containerPrefix, "container-prefix", "", "container prefix path for SonarFormatter reports")

	rootCmd.AddCommand(checkCmd)
	rootCmd.AddCommand(lintCmd)
	rootCmd.AddCommand(formatCheckCmd)
	rootCmd.AddCommand(testCmd)
}

func checkErr(err error) {
	if err != nil {
		fmt.Fprintf(os.Stderr, "❌ Error: %v\n", err)
		os.Exit(1)
	}
}
