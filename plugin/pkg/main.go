package main

import (
	"os"

	"github.com/grafana/grafana-plugin-sdk-go/backend/log"
	"github.com/grafana/grafana-plugin-sdk-go/backend/app"
	neutrinoplugin "github.com/neutrino/neutrino-app/pkg/plugin"
)

func main() {
	if err := app.Manage("neutrino-app", neutrinoplugin.NewApp, app.ManageOpts{}); err != nil {
		log.DefaultLogger.Error("Error managing app", "error", err)
		os.Exit(1)
	}
}
