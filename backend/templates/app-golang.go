package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"time"
)

type HealthResponse struct {
	Status    string `json:"status"`
	Timestamp string `json:"timestamp"`
}

type RootResponse struct {
	Message     string `json:"message"`
	Environment string `json:"environment"`
	Version     string `json:"version"`
}

func healthHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(HealthResponse{
		Status:    "healthy",
		Timestamp: time.Now().Format(time.RFC3339),
	})
}

func rootHandler(w http.ResponseWriter, r *http.Request) {
	env := os.Getenv("ENVIRONMENT")
	if env == "" {
		env = "development"
	}

	w.Header().Set("Content-Type", "text/html; charset=utf-8")
	html := fmt.Sprintf(`
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{{CUSTOMER_NAME}}</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
      background: linear-gradient(135deg, #667eea 0%%, #764ba2 100%%);
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 20px;
    }
    .container {
      background: rgba(255, 255, 255, 0.95);
      border-radius: 20px;
      box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
      padding: 60px 40px;
      text-align: center;
      max-width: 600px;
      width: 100%%;
    }
    h1 {
      font-size: 3rem;
      color: #2d3748;
      margin-bottom: 20px;
      font-weight: 800;
    }
    .subtitle {
      font-size: 1.2rem;
      color: #718096;
      margin-bottom: 40px;
    }
    .badge {
      display: inline-block;
      padding: 8px 16px;
      border-radius: 20px;
      font-size: 0.875rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
    .badge.dev { background: #48bb78; color: white; }
    .badge.preprod { background: #ed8936; color: white; }
    .badge.prod { background: #667eea; color: white; }
    .footer {
      margin-top: 40px;
      font-size: 0.875rem;
      color: #a0aec0;
    }
  </style>
</head>
<body>
  <div class="container">
    <h1>{{CUSTOMER_NAME}}</h1>
    <div class="subtitle">Application is running successfully</div>
    <div class="badge %s">%s</div>
    <div class="footer">Powered by OpenLuffy</div>
  </div>
</body>
</html>
	`, env, env)
	fmt.Fprint(w, html)
}

func main() {
	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	http.HandleFunc("/healthz", healthHandler)
	http.HandleFunc("/", rootHandler)

	env := os.Getenv("ENVIRONMENT")
	if env == "" {
		env = "development"
	}

	fmt.Printf("Starting server on port %s\n", port)
	fmt.Printf("Environment: %s\n", env)

	if err := http.ListenAndServe(":"+port, nil); err != nil {
		log.Fatal(err)
	}
}
