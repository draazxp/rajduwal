---
title: "GitOps with ArgoCD: Deploying Kubernetes Apps the Right Way"
date: 2025-03-10
description: "How to set up ArgoCD for GitOps-based continuous delivery on Kubernetes."
---

If you've been managing Kubernetes deployments manually with `kubectl apply`, you already know the pain — drift between what's in Git and what's actually running in the cluster. ArgoCD fixes that.

## What is GitOps?

GitOps is a practice where Git is the single source of truth for your infrastructure and application state. Any change you want to make goes through a pull request. The cluster automatically reconciles itself to match what's in Git.

## Why ArgoCD?

ArgoCD is a declarative, GitOps continuous delivery tool for Kubernetes. It watches your Git repo and syncs the cluster state to match it. If someone manually changes something in the cluster, ArgoCD detects the drift and can automatically revert it.

## Installing ArgoCD

```bash
# Create the namespace
kubectl create namespace argocd

# Apply the install manifest
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
```

## Creating Your First Application

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: my-app
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/your-username/your-repo
    targetRevision: HEAD
    path: k8s/
  destination:
    server: https://kubernetes.default.svc
    namespace: my-app
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

With `selfHeal: true`, ArgoCD will automatically revert any manual changes made directly to the cluster. With `prune: true`, resources removed from Git will also be removed from the cluster.

## The Workflow

1. Make a change to your Kubernetes manifests in Git
2. Open a pull request, get it reviewed
3. Merge to main
4. ArgoCD detects the change and syncs the cluster automatically

No more `kubectl apply` in CI pipelines. No more wondering what's actually deployed.
