package main

import (
	"fmt"

	"github.com/spf13/cobra"
)

var allCmd = &cobra.Command{
	Use:   "all",
	Short: "Run the complete pipeline: check (lint, format, test) followed by sonar (quality gate)",
	RunE: func(cmd *cobra.Command, args []string) error {
		fmt.Println("==========================================================")
		fmt.Println("🚀 [contas-ci] Executing Complete End-to-End Pipeline (all)")
		fmt.Println("==========================================================")

		// 1. Run check
		if err := checkCmd.RunE(cmd, args); err != nil {
			return fmt.Errorf("pipeline check stage failed: %w", err)
		}

		// 2. Run sonar
		if err := sonarCmd.RunE(cmd, args); err != nil {
			return fmt.Errorf("pipeline sonar stage failed: %w", err)
		}

		fmt.Println("==========================================================")
		fmt.Println("🎉 [contas-ci] Full Pipeline (all) COMPLETED successfully!")
		fmt.Println("==========================================================")
		return nil
	},
}

func init() {
	allCmd.Flags().StringVar(&sonarURLFlag, "sonar-url", "", "SonarQube server URL (default: $SONAR_HOST_URL or http://192.168.1.20:9000)")
	allCmd.Flags().StringVar(&tokenFlag, "token", "", "SonarQube analysis token (default: auto-resolved)")
	allCmd.Flags().BoolVar(&skipScannerFlag, "skip-scanner", false, "skip container scanner and only check existing Quality Gate")
	allCmd.Flags().StringVar(&containerEngineFlag, "container-engine", "", "container engine to use (podman or docker)")
	allCmd.Flags().BoolVar(&skipMigrationsFlag, "skip-migrations", false, "skip running database migrations before tests")
	allCmd.Flags().StringVar(&coverageFileFlag, "coverage-file", "coverage.xml", "coverage XML output file path")
	allCmd.Flags().StringVar(&testPathFlag, "test-path", "tests/unit/", "target test path or pattern")
	allCmd.Flags().StringVar(&containerPrefix, "container-prefix", "", "container prefix path for coverage files (e.g. /usr/src)")

	rootCmd.AddCommand(allCmd)
}
