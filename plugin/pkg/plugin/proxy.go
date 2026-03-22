package plugin

import (
	"fmt"
	"io"
	"net/http"
	"strings"

	"github.com/grafana/grafana-plugin-sdk-go/backend"
	"github.com/grafana/grafana-plugin-sdk-go/backend/log"
)

// proxyRequest forwards a CallResource request to the Python backend and
// writes a single buffered response back to the sender.
func proxyRequest(backendURL string, req *backend.CallResourceRequest, sender backend.CallResourceResponseSender) error {
	// Normalize path — SDK may omit the leading slash
	path := req.Path
	if !strings.HasPrefix(path, "/") {
		path = "/" + path
	}

	target := strings.TrimRight(backendURL, "/") + path

	// Append query string if present
	if req.URL != "" {
		// req.URL contains the full original URL; extract query string
		if idx := strings.Index(req.URL, "?"); idx != -1 {
			target += req.URL[idx:]
		}
	}

	httpReq, err := http.NewRequest(req.Method, target, nil)
	if err != nil {
		return fmt.Errorf("building request: %w", err)
	}

	// Forward request body
	if len(req.Body) > 0 {
		httpReq.Body = io.NopCloser(strings.NewReader(string(req.Body)))
		httpReq.ContentLength = int64(len(req.Body))
	}

	// Forward relevant headers
	for k, vals := range req.Headers {
		for _, v := range vals {
			httpReq.Header.Add(k, v)
		}
	}

	resp, err := http.DefaultClient.Do(httpReq)
	if err != nil {
		log.DefaultLogger.Error("Proxy request failed", "url", target, "error", err)
		return sender.Send(&backend.CallResourceResponse{
			Status: http.StatusBadGateway,
			Body:   []byte(`{"error":"backend unavailable"}`),
		})
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return fmt.Errorf("reading response body: %w", err)
	}

	headers := make(map[string][]string)
	for k, v := range resp.Header {
		headers[k] = v
	}

	return sender.Send(&backend.CallResourceResponse{
		Status:  resp.StatusCode,
		Headers: headers,
		Body:    body,
	})
}
