# Luffy Infrastructure - Terraform

Production-ready infrastructure as code for deploying Luffy to AWS EKS.

## Architecture

```
├── modules/
│   ├── networking/    # VPC, subnets, NAT gateways
│   ├── eks/           # EKS cluster, node groups, OIDC provider
│   ├── database/      # RDS PostgreSQL with Secrets Manager
│   └── iam/           # GitHub Actions + IRSA roles
└── environments/
    ├── dev/           # Development environment
    └── prod/          # Production environment
```

## What Gets Created

### Networking
- VPC with public + private subnets across 3 AZs
- Internet Gateway + NAT Gateways for high availability
- Route tables configured for proper traffic flow

### EKS Cluster
- Managed Kubernetes cluster (v1.31)
- Auto-scaling node groups (general + compute tiers)
- OIDC provider for IAM Roles for Service Accounts (IRSA)
- CloudWatch logging enabled

### Database
- RDS PostgreSQL 16
- Multi-AZ deployment
- Automated backups (7-day retention)
- Encrypted at rest
- Credentials stored in Secrets Manager

### IAM
- **GitHub Actions role** - OIDC-based authentication for CI/CD
- **Luffy service role** - ReadOnly AWS API access via IRSA
- Least-privilege policies for each component

## Prerequisites

1. **AWS CLI configured** with appropriate credentials
2. **Terraform >= 1.0** installed
3. **S3 backend** for state:
   ```bash
   aws s3api create-bucket \
     --bucket lebrickbot-terraform-state \
     --region us-east-1

   aws dynamodb create-table \
     --table-name lebrickbot-terraform-locks \
     --attribute-definitions AttributeName=LockID,AttributeType=S \
     --key-schema AttributeName=LockID,KeyType=HASH \
     --billing-mode PAY_PER_REQUEST
   ```

## Deployment

### Production Environment

```bash
cd terraform/environments/prod

# Initialize
terraform init

# Plan
terraform plan -out=tfplan

# Apply
terraform apply tfplan
```

### Configure kubectl

```bash
aws eks update-kubeconfig --name lebrickbot-prod --region us-east-1
```

### Bootstrap ArgoCD

```bash
# Install ArgoCD
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Install Argo Rollouts
kubectl create namespace argo-rollouts
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml

# Apply Luffy Application
kubectl apply -f ../../argocd/lebrickbot-application.yaml
```

## Cost Estimates

**Monthly (production):**
- EKS cluster: ~$73 (control plane)
- EC2 (3x t3.medium nodes): ~$90
- RDS (db.t4g.small): ~$40
- NAT Gateways (3x): ~$100
- Data transfer: ~$20
- **Total: ~$323/month**

**Savings strategies:**
- Use spot instances for compute node group
- Single NAT gateway (dev only)
- Reduce node count in off-hours

## GitHub Actions Integration

Add these secrets to your GitHub repo:

```bash
AWS_ROLE_ARN=$(terraform output -raw github_actions_role_arn)

# In GitHub: Settings → Secrets → Actions
# Add: AWS_ROLE_ARN = <value from above>
# Add: AWS_REGION = us-east-1
```

Update `.github/workflows/ci.yaml` to use OIDC:

```yaml
permissions:
  id-token: write
  contents: read

- name: Configure AWS credentials
  uses: aws-actions/configure-aws-credentials@v4
  with:
    role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
    aws-region: ${{ secrets.AWS_REGION }}
```

## Disaster Recovery

### Backup
- RDS automated backups (7 days)
- Manual snapshots before major changes
- S3 versioning on state bucket

### Restore
```bash
# From RDS snapshot
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier lebrickbot-prod-db-restored \
  --db-snapshot-identifier <snapshot-id>
```

## Security

- All traffic encrypted in transit (TLS)
- Data encrypted at rest (EBS, RDS, S3)
- Secrets managed via AWS Secrets Manager
- OIDC-based authentication (no long-lived credentials)
- IAM policies follow least-privilege principle

## Maintenance

### Update Kubernetes Version
```bash
# Update variable in prod/main.tf
cluster_version = "1.32"

terraform plan
terraform apply
```

### Scale Node Groups
```bash
# Edit node_groups in prod/main.tf
desired_size = 4

terraform apply
```

## Destroy (when ready)

```bash
cd terraform/environments/prod
terraform destroy
```

**Warning:** This will delete ALL resources including databases. Take backups first!

## Troubleshooting

### Can't authenticate to cluster
```bash
aws sts get-caller-identity  # Verify AWS credentials
aws eks update-kubeconfig --name lebrickbot-prod --region us-east-1
```

### Node group not scaling
```bash
kubectl get nodes
kubectl describe node <node-name>
aws eks describe-nodegroup --cluster-name lebrickbot-prod --nodegroup-name <name>
```

### RDS connection issues
```bash
# Check security groups
aws ec2 describe-security-groups --group-ids <rds-sg-id>

# Test from pod
kubectl run -it --rm debug --image=postgres:16 --restart=Never -- \
  psql -h <rds-endpoint> -U lebrickbot -d lebrickbot
```

---

**Questions?** Check the [main README](../../README.md) or open an issue.
