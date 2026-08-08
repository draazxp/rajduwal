---
title: "Kubernetes Sealed Secrets: Secure Your Secrets Without Losing Sleep"
date: 2025-01-15
number: 1
description: "How to encrypt Kubernetes secrets so they're safe to commit to Git, using Sealed Secrets."
---

If you're managing secrets in Kubernetes, you've probably asked yourself: "How do I keep secrets safe without messing up my workflow?"

We've all heard the horror stories — accidentally committing passwords or API keys to GitHub and exposing sensitive data. Let's talk about a better way to handle secrets: Kubernetes Sealed Secrets. It's secure, simple, and version-control friendly.

## What's Wrong with Regular Kubernetes Secrets?

Kubernetes Secrets were created to store sensitive data like passwords and API tokens. Here's what they look like:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: db-secret
type: Opaque
data:
  db_password: bXktc2VjcmV0LXBhc3N3b3Jk
```

At first glance, it looks fine. But here's the problem:

- The `db_password` is just base64 encoded, not encrypted.
- Anyone can decode it:

```bash
echo "bXktc2VjcmV0LXBhc3N3b3Jk" | base64 --decode
```

- You can't safely commit it to Git. One bad `git push`, and your secrets are out in the open.

So, how do we fix this?

## Enter Sealed Secrets: Lock It, Seal It, and Relax

Sealed Secrets solve this problem by encrypting your secrets so they can only be decrypted by your Kubernetes cluster.

Here's the magic:

1. **Encrypt with a Public Key**: Use a public key to "seal" the secret.
2. **Decrypt with a Private Key**: The private key lives safely in the cluster. Only the Sealed Secrets Controller can decrypt it.
3. **Safe to Commit**: Sealed secrets are useless to anyone without the private key. Now you can commit them to Git!

## How Sealed Secrets Work (In Plain English)

Imagine you want to lock a box (your secret).

- You have a **public key** — anyone can use it to lock the box.
- But only the **private key** (held securely by the controller in your cluster) can unlock it.

You can share the locked box (sealed secret) publicly because no one can open it without the private key.

## How to Use Sealed Secrets: Step-by-Step

### 1. Install the Tools

First, install the Sealed Secrets CLI tool, `kubeseal`, and the controller.

Install `kubeseal` on your local machine:

```bash
# macOS
brew install kubeseal

# Linux
wget https://github.com/bitnami-labs/sealed-secrets/releases/latest/download/kubeseal-linux-amd64 -O kubeseal
chmod +x kubeseal
sudo mv kubeseal /usr/local/bin/
```

Deploy the Sealed Secrets Controller to your Kubernetes cluster:

```bash
kubectl apply -f https://github.com/bitnami-labs/sealed-secrets/releases/latest/download/controller.yaml
```

### 2. Create a Secret

Start with a regular Kubernetes secret:

```bash
kubectl create secret generic db-secret \
  --from-literal=db_password=my-super-secure-password \
  --dry-run=client -o yaml > secret.yaml
```

### 3. Seal the Secret

Now, seal it using the `kubeseal` CLI:

```bash
kubeseal --format yaml < secret.yaml > sealed-secret.yaml
```

Here's what the sealed secret looks like:

```yaml
apiVersion: bitnami.com/v1alpha1
kind: SealedSecret
metadata:
  name: db-secret
spec:
  encryptedData:
    db_password: AgByaS48...super-long-encrypted-string...
```

> **Important**: Add `secret.yaml` to your `.gitignore` so plain secrets never end up in your repo.

```
**/secret.yaml
```

### 4. Deploy the Sealed Secret

Apply the sealed secret to your cluster:

```bash
kubectl apply -f sealed-secret.yaml
```

The Sealed Secrets Controller decrypts it and creates a regular Kubernetes secret that your app can use:

```bash
kubectl get secrets db-secret -o yaml
```

## How Developers Can Encrypt Secrets Without Cluster Access

Sealed Secrets are designed to be developer-friendly. Even without access to the cluster, you can still encrypt secrets using the public key.

**Step 1: Fetch the Public Key**

```bash
kubeseal --fetch-cert > public-cert.pem
```

This file can be safely shared with your team.

**Step 2: Encrypt Secrets Locally**

Anyone with the public key can create sealed secrets without cluster access:

```bash
kubeseal --cert=public-cert.pem --format yaml < secret.yaml > sealed-secret.yaml
```

The generated `sealed-secret.yaml` can be committed to Git and deployed. It stays secure because only the private key inside the cluster can decrypt it.

## Why Sealed Secrets Are Awesome

1. **Secure**: Secrets are encrypted and can't be decrypted outside the cluster.
2. **Safe for Git**: Commit your secrets without risking exposure.
3. **Cluster Controlled**: Only the controller can decrypt sealed secrets.
4. **Developer Friendly**: Encrypt secrets without direct cluster access using the public key.

## How It All Comes Together

1. **Create a Secret**: Start with plain text locally.
2. **Seal It**: Use `kubeseal` to encrypt with the public key.
3. **Add plain secrets to `.gitignore`**: Always exclude `secret.yaml` files.
4. **Commit the Sealed Secret**: Save `sealed-secret.yaml` to Git.
5. **Deploy It**: Apply it to your cluster.
6. **Decryption**: The controller decrypts it, and your app uses it securely.

## Conclusion

Kubernetes Sealed Secrets take the stress out of managing sensitive data. You can encrypt secrets, commit them safely to Git, and still ensure they're only usable inside your cluster.

Even developers without cluster access can create sealed secrets, making it a perfect fit for teams collaborating on sensitive projects.

So, the next time you need to store a database password, an API key, or a TLS certificate — don't settle for risky secrets. Seal them. Encrypt them. Sleep peacefully.
