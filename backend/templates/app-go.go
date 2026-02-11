// Sample Go HTTP Application
package main

import (
	"encoding/json"
	"log"
	"net/http"
	"os"
)

type HealthResponse struct {
	Status  string `json:"status"`
	Service string `json:"service"`
}

type MessageResponse struct {
	Message string `json:"message"`
}

func healthHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	serviceName := os.Getenv("SERVICE_NAME")
	if serviceName == "" {
		serviceName = "api"
	}
	json.NewEncoder(w).Encode(HealthResponse{
		Status:  "ok",
		Service: serviceName,
	})
}

func helloHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(MessageResponse{
		Message: "Hello from your OpenLuffy-powered application!",
	})
}

func main() {
	http.HandleFunc("/health", healthHandler)
	http.HandleFunc("/api/hello", helloHandler)

	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	log.Printf("Server running on port %s", port)
	log.Fatal(http.ListenAndServe(":"+port, nil))
}
