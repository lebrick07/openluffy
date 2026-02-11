from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from datetime import datetime
import os
import uvicorn

app = FastAPI(title="{{CUSTOMER_NAME}} API")

@app.get("/healthz")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/", response_class=HTMLResponse)
async def root():
    env = os.getenv("ENVIRONMENT", "development")
    env_class = env.lower()
    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{{{{CUSTOMER_NAME}}}}</title>
  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 20px;
    }}
    .container {{
      background: rgba(255, 255, 255, 0.95);
      border-radius: 20px;
      box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
      padding: 60px 40px;
      text-align: center;
      max-width: 600px;
      width: 100%;
    }}
    h1 {{
      font-size: 3rem;
      color: #2d3748;
      margin-bottom: 20px;
      font-weight: 800;
    }}
    .subtitle {{
      font-size: 1.2rem;
      color: #718096;
      margin-bottom: 40px;
    }}
    .badge {{
      display: inline-block;
      padding: 8px 16px;
      border-radius: 20px;
      font-size: 0.875rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }}
    .badge.dev {{ background: #48bb78; color: white; }}
    .badge.preprod {{ background: #ed8936; color: white; }}
    .badge.prod {{ background: #667eea; color: white; }}
    .footer {{
      margin-top: 40px;
      font-size: 0.875rem;
      color: #a0aec0;
    }}
  </style>
</head>
<body>
  <div class="container">
    <h1>{{{{CUSTOMER_NAME}}}}</h1>
    <div class="subtitle">Application is running successfully</div>
    <div class="badge {env_class}">{env.upper()}</div>
    <div class="footer">Powered by OpenLuffy</div>
  </div>
</body>
</html>
    """
    return html

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    print(f"Starting server on port {port}")
    print(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")
    uvicorn.run(app, host="0.0.0.0", port=port)
