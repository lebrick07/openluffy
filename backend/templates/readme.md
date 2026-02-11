# {{CUSTOMER_NAME}} - Application

> Powered by [OpenLuffy](https://github.com/lebrick07/openluffy) 🏴‍☠️

This repository was automatically initialized with a working {{STACK}} application and CI/CD pipeline.

## Quick Start

### Local Development

**{{STACK_INSTRUCTIONS}}**

### Deployment

This repository is connected to OpenLuffy's GitOps pipeline:

- **Development**: Pushes to `develop` branch auto-deploy to `dev.{{CUSTOMER_ID}}.local`
- **Pre-Production**: Automatic promotion after dev validation → `preprod.{{CUSTOMER_ID}}.local`
- **Production**: Manual approval required → `{{CUSTOMER_ID}}.local`

### CI/CD Pipeline

GitHub Actions workflow (`.github/workflows/ci.yaml`) automatically:
1. Runs tests
2. Builds Docker image
3. Pushes to GitHub Container Registry
4. Triggers ArgoCD sync

### ArgoCD

View deployment status: [http://argocd.local](http://argocd.local)

Applications:
- `{{CUSTOMER_ID}}-dev`
- `{{CUSTOMER_ID}}-preprod`
- `{{CUSTOMER_ID}}-prod`

### API Endpoints

- **Health Check**: `GET /health`
- **Hello World**: `GET /api/hello`

Add your own endpoints to the application!

## Support

Managed by OpenLuffy DevOps Platform.
