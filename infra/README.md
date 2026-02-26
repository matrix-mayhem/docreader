# Infrastructure Learning Pack

This folder contains **teaching-oriented** examples for a complete platform delivery workflow:

- `Dockerfile`: multi-stage container build, non-root runtime, healthchecks, and signal handling.
- `Jenkinsfile`: classic CI/CD pipeline with stages for tests, image build, scanning, Terraform, and Kubernetes checks.
- `.github/workflows/ci-cd.yml`: GitHub Actions equivalent with job dependencies and environment gates.
- `terraform/`: AWS ECS + ALB + ECR reference architecture to learn IaC foundations.
- `k8s/`: production-style Kubernetes manifests (Deployment, Service, Ingress, HPA, PDB, NetworkPolicy).

## Suggested learning order

1. Start with Docker and run the API in a local container.
2. Compare Jenkins and GitHub Actions to understand platform-agnostic CI/CD concepts.
3. Review Terraform graph in `infra/terraform` and inspect how networking, IAM, and ECS connect.
4. Apply Kubernetes manifests to a local cluster (kind/minikube) and observe scaling behavior with HPA.

## Local commands

```bash
# Docker
docker build -t financial-analytics-api:local .
docker run --rm -p 8000:8000 financial-analytics-api:local

# Terraform (safe validation mode)
cd infra/terraform
terraform init -backend=false
terraform fmt -recursive
terraform validate

# Kubernetes apply
kubectl apply -f infra/k8s/namespace.yaml
kubectl apply -f infra/k8s/
```
