---
title: "Kubernetes Sealed Secrets: Secure Your Secrets Without Losing Sleep"
date: 2025-01-15
description: "A guide to using Sealed Secrets in Kubernetes to keep your secrets safe in Git."
---

This is a sample post to test the blog build system. Replace this content with your actual blog post, or delete this file and create your own.

## Why Sealed Secrets?

Managing secrets in Kubernetes can be tricky — you want them in version control for reproducibility, but you can't just commit plaintext secrets to Git.

Sealed Secrets solves this by encrypting your secrets so they can only be decrypted by the controller running in your cluster.

## How It Works

1. You create a regular Kubernetes Secret manifest
2. You encrypt it using `kubeseal` CLI
3. The encrypted SealedSecret is safe to commit to Git
4. The controller in your cluster decrypts it back into a regular Secret

## Getting Started

```bash
# Install kubeseal CLI
brew install kubeseal

# Seal a secret
kubeseal --format yaml < my-secret.yaml > my-sealed-secret.yaml
```

That's the gist of it. For the full deep-dive, check out the [original post on Medium](https://medium.com/@draazxp/kubernetes-sealed-secrets-secure-your-secrets-without-losing-sleep-964ef18d9984).
