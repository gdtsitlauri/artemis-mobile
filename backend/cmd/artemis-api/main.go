package main

import (
	"log"
	"net/http"
	"os"

	"artemis/backend/internal/server"
)

func main() {
	addr := ":8080"
	if value := os.Getenv("ARTEMIS_ADDR"); value != "" {
		addr = value
	}
	store := server.NewStore()
	log.Printf("starting ARTEMIS backend on %s", addr)
	if err := http.ListenAndServe(addr, server.Handler(store)); err != nil {
		log.Fatal(err)
	}
}
