package sonar

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"strings"
	"time"
)

// SonarClient provides methods to interact with the SonarQube REST API.
type SonarClient struct {
	BaseURL    string
	Token      string
	HTTPClient *http.Client
}

func NewSonarClient(baseURL, token string) *SonarClient {
	return &SonarClient{
		BaseURL: strings.TrimRight(baseURL, "/"),
		Token:   token,
		HTTPClient: &http.Client{
			Timeout: 15 * time.Second,
		},
	}
}

// SetBasicAuth sets standard SonarQube token authentication (token as username, empty password).
func (c *SonarClient) setAuth(req *http.Request) {
	if c.Token != "" {
		req.SetBasicAuth(c.Token, "")
	}
}

// WaitForServerUp checks /api/system/status until status is UP or maxAttempts exceeded.
func (c *SonarClient) WaitForServerUp(ctx context.Context, maxAttempts int, retryDelay time.Duration) error {
	endpoint := fmt.Sprintf("%s/api/system/status", c.BaseURL)

	for attempt := 1; attempt <= maxAttempts; attempt++ {
		req, err := http.NewRequestWithContext(ctx, http.MethodGet, endpoint, nil)
		if err != nil {
			return err
		}

		resp, err := c.HTTPClient.Do(req)
		if err == nil {
			defer resp.Body.Close()
			if resp.StatusCode == http.StatusOK {
				var statusResp struct {
					Status string `json:"status"`
				}
				if json.NewDecoder(resp.Body).Decode(&statusResp) == nil && statusResp.Status == "UP" {
					return nil
				}
			}
		}

		select {
		case <-ctx.Done():
			return ctx.Err()
		case <-time.After(retryDelay):
		}
	}

	return fmt.Errorf("server at %s did not become UP after %d attempts", c.BaseURL, maxAttempts)
}

// SetupEphemeralCIAuth bootstraps authentication for ephemeral CI containers (admin:admin -> admin1234 -> token).
func (c *SonarClient) SetupEphemeralCIAuth(ctx context.Context) (string, error) {
	// 1. Try to change initial password admin -> admin1234
	changePassURL := fmt.Sprintf("%s/api/users/change_password?login=admin&previousPassword=admin&password=admin1234", c.BaseURL)
	req, _ := http.NewRequestWithContext(ctx, http.MethodPost, changePassURL, nil)
	req.SetBasicAuth("admin", "admin")
	if resp, err := c.HTTPClient.Do(req); err == nil {
		resp.Body.Close()
	}

	// 2. Generate analysis token using admin1234
	genTokenURL := fmt.Sprintf("%s/api/user_tokens/generate?name=ci-token-%d", c.BaseURL, time.Now().Unix())
	req, _ = http.NewRequestWithContext(ctx, http.MethodPost, genTokenURL, nil)
	req.SetBasicAuth("admin", "admin1234")
	resp, err := c.HTTPClient.Do(req)
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusOK {
		var tokenResp struct {
			Token string `json:"token"`
		}
		if json.NewDecoder(resp.Body).Decode(&tokenResp) == nil && tokenResp.Token != "" {
			c.Token = tokenResp.Token
			return tokenResp.Token, nil
		}
	}

	return "", fmt.Errorf("failed to generate ephemeral analysis token")
}

// ValidateToken checks if the provided token is valid in the SonarQube instance.
func (c *SonarClient) ValidateToken(ctx context.Context) (bool, error) {
	endpoint := fmt.Sprintf("%s/api/authentication/validate", c.BaseURL)
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, endpoint, nil)
	if err != nil {
		return false, err
	}
	c.setAuth(req)

	resp, err := c.HTTPClient.Do(req)
	if err != nil {
		return false, fmt.Errorf("authentication check failed: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return false, fmt.Errorf("unexpected status code %d from auth validate", resp.StatusCode)
	}

	var authResp struct {
		Valid bool `json:"valid"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&authResp); err != nil {
		return false, err
	}

	return authResp.Valid, nil
}

// EnsureProjectExists creates the project if it does not already exist.
func (c *SonarClient) EnsureProjectExists(ctx context.Context, projectKey, projectName string) error {
	endpoint := fmt.Sprintf("%s/api/projects/create", c.BaseURL)
	form := url.Values{}
	form.Set("name", projectName)
	form.Set("project", projectKey)

	req, err := http.NewRequestWithContext(ctx, http.MethodPost, endpoint, strings.NewReader(form.Encode()))
	if err != nil {
		return err
	}
	req.Header.Set("Content-Type", "application/x-www-form-urlencoded")
	c.setAuth(req)

	resp, err := c.HTTPClient.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	// 200 OK or 400 (already exists) are accepted
	if resp.StatusCode == http.StatusOK || resp.StatusCode == http.StatusBadRequest {
		return nil
	}

	body, _ := io.ReadAll(resp.Body)
	return fmt.Errorf("failed to create project '%s' (status %d): %s", projectKey, resp.StatusCode, string(body))
}

// SetupQualityProfile ensures the custom Quality Profile exists, inherits from Sonar way, and activates formatting rules.
func (c *SonarClient) SetupQualityProfile(ctx context.Context, projectKey, profileName string) error {
	// 1. Create quality profile
	createURL := fmt.Sprintf("%s/api/qualityprofiles/create", c.BaseURL)
	form := url.Values{
		"language": {"py"},
		"name":     {profileName},
	}
	req, _ := http.NewRequestWithContext(ctx, http.MethodPost, createURL, strings.NewReader(form.Encode()))
	req.Header.Set("Content-Type", "application/x-www-form-urlencoded")
	c.setAuth(req)
	if resp, err := c.HTTPClient.Do(req); err == nil {
		resp.Body.Close()
	}

	// 2. Change parent to Sonar way
	changeParentURL := fmt.Sprintf("%s/api/qualityprofiles/change_parent", c.BaseURL)
	form = url.Values{
		"language":             {"py"},
		"qualityProfile":       {profileName},
		"parentQualityProfile": {"Sonar way"},
	}
	req, _ = http.NewRequestWithContext(ctx, http.MethodPost, changeParentURL, strings.NewReader(form.Encode()))
	req.Header.Set("Content-Type", "application/x-www-form-urlencoded")
	c.setAuth(req)
	if resp, err := c.HTTPClient.Do(req); err == nil {
		resp.Body.Close()
	}

	// 3. Search for profile key
	searchURL := fmt.Sprintf("%s/api/qualityprofiles/search?language=py", c.BaseURL)
	req, _ = http.NewRequestWithContext(ctx, http.MethodGet, searchURL, nil)
	c.setAuth(req)
	resp, err := c.HTTPClient.Do(req)
	if err != nil {
		return fmt.Errorf("failed to search quality profiles: %w", err)
	}
	defer resp.Body.Close()

	var searchResp struct {
		Profiles []struct {
			Key  string `json:"key"`
			Name string `json:"name"`
		} `json:"profiles"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&searchResp); err != nil {
		return err
	}

	var profileKey string
	for _, p := range searchResp.Profiles {
		if p.Name == profileName {
			profileKey = p.Key
			break
		}
	}

	if profileKey == "" {
		return nil // profile not found, continue with default
	}

	// 4. Activate rule python:S113 (End of file formatting)
	activateURL := fmt.Sprintf("%s/api/qualityprofiles/activate_rule", c.BaseURL)
	form = url.Values{
		"key":      {profileKey},
		"rule":     {"python:S113"},
		"severity": {"MAJOR"},
	}
	req, _ = http.NewRequestWithContext(ctx, http.MethodPost, activateURL, strings.NewReader(form.Encode()))
	req.Header.Set("Content-Type", "application/x-www-form-urlencoded")
	c.setAuth(req)
	if resp, err := c.HTTPClient.Do(req); err == nil {
		resp.Body.Close()
	}

	// 5. Add project to quality profile
	addProjectURL := fmt.Sprintf("%s/api/qualityprofiles/add_project", c.BaseURL)
	form = url.Values{
		"language":       {"py"},
		"qualityProfile": {profileName},
		"project":        {projectKey},
	}
	req, _ = http.NewRequestWithContext(ctx, http.MethodPost, addProjectURL, strings.NewReader(form.Encode()))
	req.Header.Set("Content-Type", "application/x-www-form-urlencoded")
	c.setAuth(req)
	if resp, err := c.HTTPClient.Do(req); err == nil {
		resp.Body.Close()
	}

	return nil
}
