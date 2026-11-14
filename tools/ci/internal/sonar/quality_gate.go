package sonar

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"time"
)

// WaitForComputeEngineTask polls /api/ce/component until current task is finished (or queue is empty).
func (c *SonarClient) WaitForComputeEngineTask(ctx context.Context, projectKey string, maxAttempts int, retryDelay time.Duration) error {
	endpoint := fmt.Sprintf("%s/api/ce/component?component=%s", c.BaseURL, projectKey)

	for attempt := 1; attempt <= maxAttempts; attempt++ {
		req, err := http.NewRequestWithContext(ctx, http.MethodGet, endpoint, nil)
		if err != nil {
			return err
		}
		c.setAuth(req)

		resp, err := c.HTTPClient.Do(req)
		if err == nil {
			defer resp.Body.Close()
			if resp.StatusCode == http.StatusOK {
				var ceResp struct {
					Current struct {
						Status string `json:"status"`
					} `json:"current"`
					Queue []interface{} `json:"queue"`
				}
				if json.NewDecoder(resp.Body).Decode(&ceResp) == nil {
					status := ceResp.Current.Status
					if status == "SUCCESS" || (status == "" && len(ceResp.Queue) == 0) {
						return nil
					}
					if status == "FAILED" || status == "CANCELED" {
						return fmt.Errorf("sonar compute engine task %s", status)
					}
				}
			}
		}

		select {
		case <-ctx.Done():
			return ctx.Err()
		case <-time.After(retryDelay):
		}
	}

	return fmt.Errorf("sonar analysis processing did not finish within timeout (%d attempts)", maxAttempts)
}

// GetQualityGateStatus retrieves the project status (OK or ERROR) from SonarQube.
func (c *SonarClient) GetQualityGateStatus(ctx context.Context, projectKey string) (string, error) {
	endpoint := fmt.Sprintf("%s/api/qualitygates/project_status?projectKey=%s", c.BaseURL, projectKey)
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, endpoint, nil)
	if err != nil {
		return "ERROR", err
	}
	c.setAuth(req)

	resp, err := c.HTTPClient.Do(req)
	if err != nil {
		return "ERROR", fmt.Errorf("failed to fetch quality gate status: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return "ERROR", fmt.Errorf("unexpected status code %d from quality gate", resp.StatusCode)
	}

	var qgResp struct {
		ProjectStatus struct {
			Status string `json:"status"`
		} `json:"projectStatus"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&qgResp); err != nil {
		return "ERROR", err
	}

	return qgResp.ProjectStatus.Status, nil
}
