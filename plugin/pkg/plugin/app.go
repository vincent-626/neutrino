package plugin

import (
	"context"
	"net/http"
	"os"

	"github.com/grafana/grafana-plugin-sdk-go/backend"
	"github.com/grafana/grafana-plugin-sdk-go/backend/instancemgmt"
	"github.com/grafana/grafana-plugin-sdk-go/backend/log"
)

const defaultBackendURL = "http://localhost:8400"

// App implements the Grafana app plugin backend.
type App struct {
	backend.CallResourceHandlerFunc
	backendURL string
}

// NewApp is called by the SDK when a new plugin instance is needed.
func NewApp(_ context.Context, _ backend.AppInstanceSettings) (instancemgmt.Instance, error) {
	backendURL := os.Getenv("NEUTRINO_BACKEND_URL")
	if backendURL == "" {
		backendURL = defaultBackendURL
	}

	log.DefaultLogger.Info("Neutrino app started", "backendURL", backendURL)

	a := &App{backendURL: backendURL}
	a.CallResourceHandlerFunc = backend.CallResourceHandlerFunc(a.callResource)
	return a, nil
}

// CallResource is the main entry point for all frontend → plugin HTTP calls.
func (a *App) CallResource(ctx context.Context, req *backend.CallResourceRequest, sender backend.CallResourceResponseSender) error {
	return a.callResource(ctx, req, sender)
}

func (a *App) callResource(_ context.Context, req *backend.CallResourceRequest, sender backend.CallResourceResponseSender) error {
	// Only allow safe resource paths
	switch {
	case req.Path == "search" || req.Path == "/search":
		if req.Method != http.MethodPost {
			return sender.Send(&backend.CallResourceResponse{
				Status: http.StatusMethodNotAllowed,
			})
		}
	case req.Path == "labels" || req.Path == "/labels":
		if req.Method != http.MethodGet {
			return sender.Send(&backend.CallResourceResponse{
				Status: http.StatusMethodNotAllowed,
			})
		}
	case req.Path == "healthz" || req.Path == "/healthz",
		req.Path == "readyz" || req.Path == "/readyz":
		// pass-through
	default:
		return sender.Send(&backend.CallResourceResponse{
			Status: http.StatusNotFound,
		})
	}

	return proxyRequest(a.backendURL, req, sender)
}

// Dispose is called when the instance is removed.
func (a *App) Dispose() {}
