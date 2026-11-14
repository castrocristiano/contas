package main

import (
	"context"
	"fmt"
	"os"
	"strings"
	"time"

	"github.com/spf13/cobra"

	"contas/tools/ci/internal/config"
	"contas/tools/ci/internal/pipeline"
	"contas/tools/ci/internal/runner"
	"contas/tools/ci/internal/sonar"
)

var (
	sonarURLFlag        string
	tokenFlag           string
	skipScannerFlag     bool
	containerEngineFlag string
	timeoutFlag         time.Duration
)

var sonarCmd = &cobra.Command{
	Use:   "sonar",
	Short: "Run complete SonarQube quality analysis and Quality Gate validation",
	RunE: func(cmd *cobra.Command, args []string) error {
		dir, err := resolveProjectDir()
		if err != nil {
			return err
		}

		ctx := context.Background()
		exec := runner.NewDefaultExecutor()

		// 1. Resolve Sonar Host URL
		sonarURL := sonarURLFlag
		if sonarURL == "" {
			if envURL := os.Getenv("SONAR_HOST_URL"); envURL != "" {
				sonarURL = envURL
			} else {
				sonarURL = "http://192.168.1.20:9000"
			}
		}

		// 2. Resolve Sonar Token
		token := tokenFlag
		if token == "" {
			token, _, _ = config.ResolveSonarToken(dir)
		}

		client := sonar.NewSonarClient(sonarURL, token)

		fmt.Println("==========================================================")
		fmt.Printf("🛡️  [contas-ci] Executing SonarQube Analysis (%s)\n", sonarURL)
		fmt.Println("==========================================================")

		// 3. Verify server status (UP)
		fmt.Printf("⏳ [contas-ci] Checking SonarQube server readiness at %s...\n", sonarURL)
		if err := client.WaitForServerUp(ctx, 40, 3*time.Second); err != nil {
			return fmt.Errorf("sonar server unreachable: %w", err)
		}
		fmt.Println("✅ [contas-ci] SonarQube server is ready!")

		// 4. Validate or bootstrap Token
		valid, _ := client.ValidateToken(ctx)
		if !valid {
			// If running against localhost or ephemeral container, try bootstrapping CI auth
			if strings.Contains(sonarURL, "localhost") || strings.Contains(sonarURL, "127.0.0.1") {
				fmt.Println("⚙️  [contas-ci] Bootstrapping ephemeral CI authentication...")
				generatedToken, err := client.SetupEphemeralCIAuth(ctx)
				if err == nil && generatedToken != "" {
					token = generatedToken
					valid = true
					fmt.Println("✅ [contas-ci] Ephemeral CI token generated successfully!")
				}
			}
		}

		if !valid {
			return fmt.Errorf("SONAR_TOKEN is missing or invalid for %s (check environment or .env)", sonarURL)
		}
		_ = config.PersistRemoteToken(dir, token)

		// 5. Ensure Project and Quality Profile exist
		projectKey := "contas"
		if err := client.EnsureProjectExists(ctx, projectKey, projectKey); err != nil {
			fmt.Printf("⚠️  [contas-ci] Notice on project creation: %v\n", err)
		}

		profileName := "Contas Python (Sonar way + Formatter)"
		if err := client.SetupQualityProfile(ctx, projectKey, profileName); err != nil {
			fmt.Printf("⚠️  [contas-ci] Notice on quality profile setup: %v\n", err)
		}

		// 6. Generate Formatter reports
		if err := pipeline.RunFormatCheck(ctx, exec, dir, "/usr/src"); err != nil {
			fmt.Printf("⚠️  [contas-ci] Formatter check notice: %v\n", err)
		}

		// 7. Execute SonarScanner container
		if !skipScannerFlag {
			scannerOpts := sonar.ScannerOptions{
				SonarHostURL:    sonarURL,
				SonarToken:      token,
				ProjectKey:      projectKey,
				ContainerEngine: containerEngineFlag,
				ProjectDir:      dir,
			}
			if err := sonar.RunSonarScanner(ctx, exec, scannerOpts); err != nil {
				return err
			}
		}

		// 8. Wait for Compute Engine processing
		fmt.Println("🚦 [contas-ci] Waiting for SonarQube analysis processing...")
		if err := client.WaitForComputeEngineTask(ctx, projectKey, 35, 2*time.Second); err != nil {
			return fmt.Errorf("error processing analysis task: %w", err)
		}

		// 9. Evaluate Quality Gate status
		qgStatus, err := client.GetQualityGateStatus(ctx, projectKey)
		if err != nil {
			return err
		}

		fmt.Println("==========================================================")
		if qgStatus == "OK" {
			fmt.Printf("🎉 [contas-ci] SUCCESS: Quality Gate APPROVED on %s!\n", sonarURL)
			fmt.Printf("📊 Dashboard: %s/dashboard?id=%s\n", sonarURL, projectKey)
			fmt.Println("==========================================================")
			return nil
		}

		fmt.Printf("🛑 [contas-ci] FAILURE: Quality Gate status is %s on %s.\n", qgStatus, sonarURL)
		fmt.Printf("📊 Dashboard: %s/dashboard?id=%s\n", sonarURL, projectKey)
		fmt.Println("==========================================================")
		return fmt.Errorf("quality gate failed with status %s", qgStatus)
	},
}

func init() {
	sonarCmd.Flags().StringVar(&sonarURLFlag, "sonar-url", "", "SonarQube server URL (default: $SONAR_HOST_URL or http://192.168.1.20:9000)")
	sonarCmd.Flags().StringVar(&tokenFlag, "token", "", "SonarQube analysis token (default: auto-resolved)")
	sonarCmd.Flags().BoolVar(&skipScannerFlag, "skip-scanner", false, "skip container scanner and only check existing Quality Gate")
	sonarCmd.Flags().StringVar(&containerEngineFlag, "container-engine", "", "container engine to use (podman or docker)")
	sonarCmd.Flags().DurationVar(&timeoutFlag, "timeout", 5*time.Minute, "timeout duration for processing")

	rootCmd.AddCommand(sonarCmd)
}
