package config

import (
	"bufio"
	"fmt"
	"os"
	"path/filepath"
	"strings"
)

// ResolveSonarToken attempts to resolve the SonarQube authentication token
// following the project priority:
// 1. Environment variable SONAR_TOKEN
// 2. Variable SONAR_TOKEN inside .env in projectDir
// 3. Content of .sonar_token in projectDir
// 4. Content of .sonar_remote_token in projectDir
func ResolveSonarToken(projectDir string) (string, string, error) {
	// 1. Environment variable
	if envToken := strings.TrimSpace(os.Getenv("SONAR_TOKEN")); envToken != "" {
		return envToken, "environment variable SONAR_TOKEN", nil
	}

	// 2. .env file
	envPath := filepath.Join(projectDir, ".env")
	if token, err := extractTokenFromEnvFile(envPath); err == nil && token != "" {
		return token, ".env file", nil
	}

	// 3. .sonar_token file
	tokenPath := filepath.Join(projectDir, ".sonar_token")
	if token, err := readTokenFile(tokenPath); err == nil && token != "" {
		return token, ".sonar_token file", nil
	}

	// 4. .sonar_remote_token file
	remoteTokenPath := filepath.Join(projectDir, ".sonar_remote_token")
	if token, err := readTokenFile(remoteTokenPath); err == nil && token != "" {
		return token, ".sonar_remote_token file", nil
	}

	return "", "", fmt.Errorf("SONAR_TOKEN not found (checked environment, .env, .sonar_token and .sonar_remote_token)")
}

// PersistRemoteToken saves the resolved token into .sonar_remote_token with restricted 0600 permissions.
func PersistRemoteToken(projectDir, token string) error {
	remoteTokenPath := filepath.Join(projectDir, ".sonar_remote_token")
	return os.WriteFile(remoteTokenPath, []byte(strings.TrimSpace(token)+"\n"), 0600)
}

func extractTokenFromEnvFile(path string) (string, error) {
	file, err := os.Open(path)
	if err != nil {
		return "", err
	}
	defer file.Close()

	var lastFound string
	scanner := bufio.NewScanner(file)
	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())
		if strings.HasPrefix(line, "#") {
			continue
		}
		if strings.HasPrefix(line, "SONAR_TOKEN=") {
			val := strings.TrimPrefix(line, "SONAR_TOKEN=")
			val = strings.TrimSpace(val)
			val = strings.Trim(val, `"'`)
			if val != "" {
				lastFound = val
			}
		}
	}
	if err := scanner.Err(); err != nil {
		return "", err
	}
	return lastFound, nil
}

func readTokenFile(path string) (string, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return "", err
	}
	return strings.TrimSpace(string(data)), nil
}
