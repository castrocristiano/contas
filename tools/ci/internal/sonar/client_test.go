package sonar

import (
	"context"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"
)

func TestSonarClient_WaitForServerUp(t *testing.T) {
	attempts := 0
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/api/system/status" {
			attempts++
			if attempts < 2 {
				w.WriteHeader(http.StatusOK)
				w.Write([]byte(`{"status":"STARTING"}`))
				return
			}
			w.WriteHeader(http.StatusOK)
			w.Write([]byte(`{"status":"UP"}`))
			return
		}
		http.NotFound(w, r)
	}))
	defer server.Close()

	client := NewSonarClient(server.URL, "dummy-token")
	err := client.WaitForServerUp(context.Background(), 5, 10*time.Millisecond)
	if err != nil {
		t.Fatalf("expected WaitForServerUp to succeed, got: %v", err)
	}
}

func TestSonarClient_ValidateToken(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/api/authentication/validate" {
			user, _, ok := r.BasicAuth()
			if ok && user == "valid-token" {
				w.WriteHeader(http.StatusOK)
				w.Write([]byte(`{"valid":true}`))
				return
			}
			w.WriteHeader(http.StatusOK)
			w.Write([]byte(`{"valid":false}`))
			return
		}
		http.NotFound(w, r)
	}))
	defer server.Close()

	client := NewSonarClient(server.URL, "valid-token")
	valid, err := client.ValidateToken(context.Background())
	if err != nil || !valid {
		t.Fatalf("expected token to be valid, got valid=%v, err=%v", valid, err)
	}

	clientInvalid := NewSonarClient(server.URL, "invalid-token")
	valid, err = clientInvalid.ValidateToken(context.Background())
	if err != nil || valid {
		t.Fatalf("expected token to be invalid, got valid=%v, err=%v", valid, err)
	}
}

func TestSonarClient_GetQualityGateStatus(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/api/qualitygates/project_status" {
			w.WriteHeader(http.StatusOK)
			w.Write([]byte(`{"projectStatus":{"status":"OK"}}`))
			return
		}
		http.NotFound(w, r)
	}))
	defer server.Close()

	client := NewSonarClient(server.URL, "valid-token")
	status, err := client.GetQualityGateStatus(context.Background(), "contas")
	if err != nil || status != "OK" {
		t.Fatalf("expected Quality Gate status 'OK', got %s (err: %v)", status, err)
	}
}
