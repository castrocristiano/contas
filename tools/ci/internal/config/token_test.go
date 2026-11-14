package config

import (
	"os"
	"path/filepath"
	"testing"
)

func TestResolveSonarToken(t *testing.T) {
	tempDir := t.TempDir()

	// Case 1: Priority 1 - Environment variable
	os.Setenv("SONAR_TOKEN", "token-from-env")
	token, source, err := ResolveSonarToken(tempDir)
	if err != nil || token != "token-from-env" {
		t.Fatalf("expected token-from-env, got %s (err: %v)", token, err)
	}
	if source != "environment variable SONAR_TOKEN" {
		t.Errorf("unexpected source: %s", source)
	}
	os.Unsetenv("SONAR_TOKEN")

	// Case 2: Priority 2 - .env file
	envFile := filepath.Join(tempDir, ".env")
	err = os.WriteFile(envFile, []byte("OTHER_VAR=123\nSONAR_TOKEN=\"token-from-dotenv\"\n"), 0644)
	if err != nil {
		t.Fatal(err)
	}
	token, source, err = ResolveSonarToken(tempDir)
	if err != nil || token != "token-from-dotenv" {
		t.Fatalf("expected token-from-dotenv, got %s (err: %v)", token, err)
	}
	if source != ".env file" {
		t.Errorf("unexpected source: %s", source)
	}
	os.Remove(envFile)

	// Case 3: Priority 3 - .sonar_token file
	sonarTokenFile := filepath.Join(tempDir, ".sonar_token")
	err = os.WriteFile(sonarTokenFile, []byte("  token-from-file  \n"), 0600)
	if err != nil {
		t.Fatal(err)
	}
	token, source, err = ResolveSonarToken(tempDir)
	if err != nil || token != "token-from-file" {
		t.Fatalf("expected token-from-file, got %s (err: %v)", token, err)
	}
	if source != ".sonar_token file" {
		t.Errorf("unexpected source: %s", source)
	}
	os.Remove(sonarTokenFile)

	// Case 4: Priority 4 - .sonar_remote_token file
	remoteFile := filepath.Join(tempDir, ".sonar_remote_token")
	err = os.WriteFile(remoteFile, []byte("token-from-remote-file"), 0600)
	if err != nil {
		t.Fatal(err)
	}
	token, source, err = ResolveSonarToken(tempDir)
	if err != nil || token != "token-from-remote-file" {
		t.Fatalf("expected token-from-remote-file, got %s (err: %v)", token, err)
	}
	if source != ".sonar_remote_token file" {
		t.Errorf("unexpected source: %s", source)
	}
	os.Remove(remoteFile)

	// Case 5: Missing token error
	_, _, err = ResolveSonarToken(tempDir)
	if err == nil {
		t.Fatalf("expected error when no token sources exist, got nil")
	}
}

func TestPersistRemoteToken(t *testing.T) {
	tempDir := t.TempDir()
	err := PersistRemoteToken(tempDir, "sqp_secret_token_123")
	if err != nil {
		t.Fatalf("unexpected error persisting token: %v", err)
	}

	tokenPath := filepath.Join(tempDir, ".sonar_remote_token")
	info, err := os.Stat(tokenPath)
	if err != nil {
		t.Fatalf("failed to stat persisted token file: %v", err)
	}

	// Verify permissions (0600)
	if perm := info.Mode().Perm(); perm != 0600 {
		t.Errorf("expected 0600 permissions, got %o", perm)
	}

	content, err := os.ReadFile(tokenPath)
	if err != nil || string(content) != "sqp_secret_token_123\n" {
		t.Errorf("unexpected file content: %s", string(content))
	}
}
