package main

import (
	"os"

	"github.com/jessevdk/go-flags"
)

func main() {
	var options struct{} // No common flags

	parser := flags.NewParser(&options, flags.Default)

	parser.AddCommand("search",
		"Search for libraries associated with specific terms",
		"Search for libraries associated with specific terms",
		&SearchCommand{})

	parser.AddCommand("install",
		"Install named libraries",
		"Install named libraries",
		&InstallCommand{})

	parser.AddCommand("index",
		"Build library index",
		"Build library index",
		&IndexCommand{})

	parser.AddCommand("version",
		"Version information about impact itself",
		"Version information about impact itself",
		&VersionCommand{})

	if _, err := parser.Parse(); err != nil {
		os.Exit(1)
	}
}
