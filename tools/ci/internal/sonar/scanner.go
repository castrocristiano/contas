package sonar

import (
	"context"
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"contas/tools/ci/internal/runner"
)

type ScannerOptions struct {
	SonarHostURL    string
	SonarToken      string
	ProjectKey      string
	ContainerEngine string
	ProjectDir      string
	CoverageFile    string
	RuffReport      string
	FormatterIssues string
}

// DetectContainerEngine checks for podman first, then docker.
func DetectContainerEngine(exec runner.CommandExecutor, override string) (string, error) {
	if override != "" {
		return override, nil
	}
	if _, err := exec.LookPath("podman"); err == nil {
		return "podman", nil
	}
	if _, err := exec.LookPath("docker"); err == nil {
		return "docker", nil
	}
	return "", fmt.Errorf("neither podman nor docker found in PATH for containerized SonarScanner")
}

// NormalizeCoveragePaths adjusts file paths in coverage.xml to match the container's /usr/src mount point.
func NormalizeCoveragePaths(projectDir, coverageFile string) error {
	path := filepath.Join(projectDir, coverageFile)
	data, err := os.ReadFile(path)
	if err != nil {
		return nil // if coverage file doesn't exist, skip silently
	}

	content := string(data)
	// Replace host path with container mount path /usr/src
	content = strings.ReplaceAll(content, projectDir+"/src", "/usr/src/src")
	content = strings.ReplaceAll(content, projectDir, "/usr/src")

	return os.WriteFile(path, []byte(content), 0644)
}

// RunSonarScanner launches the official SonarScanner container.
func RunSonarScanner(ctx context.Context, exec runner.CommandExecutor, opts ScannerOptions) error {
	engine, err := DetectContainerEngine(exec, opts.ContainerEngine)
	if err != nil {
		return err
	}

	coverageFile := opts.CoverageFile
	if coverageFile == "" {
		coverageFile = "coverage.xml"
	}
	ruffReport := opts.RuffReport
	if ruffReport == "" {
		ruffReport = "ruff-report.json"
	}
	formatterIssues := opts.FormatterIssues
	if formatterIssues == "" {
		formatterIssues = "sonar-formatter-issues.json"
	}

	// Normalize coverage.xml paths for the container scanner
	if err := NormalizeCoveragePaths(opts.ProjectDir, coverageFile); err != nil {
		fmt.Printf("⚠️  [contas-ci] Failed to normalize coverage paths: %v\n", err)
	}

	fmt.Printf("🔍 [contas-ci] Running SonarScanner container via %s pointing to %s...\n", engine, opts.SonarHostURL)

	scannerArgs := []string{
		"run", "--rm",
		"-v", fmt.Sprintf("%s:/usr/src:Z", opts.ProjectDir),
		"--network", "host",
		"docker.io/sonarsource/sonar-scanner-cli:latest",
		fmt.Sprintf("-Dsonar.host.url=%s", opts.SonarHostURL),
		fmt.Sprintf("-Dsonar.token=%s", opts.SonarToken),
		fmt.Sprintf("-Dsonar.projectKey=%s", opts.ProjectKey),
		"-Dsonar.sources=src",
		"-Dsonar.tests=tests",
		fmt.Sprintf("-Dsonar.python.coverage.reportPaths=%s", coverageFile),
		fmt.Sprintf("-Dsonar.python.ruff.reportPaths=%s", ruffReport),
		fmt.Sprintf("-Dsonar.externalIssuesReportPaths=%s", formatterIssues),
		"-Dsonar.exclusions=**/__pycache__/**,**/*.pyc,**/.venv/**,**/alembic/versions/**,**/docker/keycloak/**",
		"-Dsonar.coverage.exclusions=tests/**,**/alembic/**,**/__init__.py,**/ui/app.py,**/ui/views/**,**/__main__.py",
	}

	execOpts := runner.ExecutionOptions{
		Command:      engine,
		Args:         scannerArgs,
		WorkingDir:   opts.ProjectDir,
		StreamOutput: true,
	}

	_, err = exec.Run(ctx, execOpts)
	if err != nil {
		return fmt.Errorf("sonar scanner execution failed: %w", err)
	}

	fmt.Println("✅ [contas-ci] SonarScanner execution completed successfully!")
	return nil
}
