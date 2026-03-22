//go:build mage
// +build mage

package main

import "github.com/grafana/grafana-plugin-sdk-go/build"

var b build.Build

// Linux builds the backend plugin binary for linux/amd64.
func Linux() error { return b.Linux() }

// LinuxARM64 builds the backend plugin binary for linux/arm64.
func LinuxARM64() error { return b.LinuxARM64() }

// Clean removes build artifacts.
func Clean() error { return build.Clean() }
