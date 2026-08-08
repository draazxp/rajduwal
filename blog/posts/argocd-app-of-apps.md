---
title: "ArgoCD App of Apps: The King of Kings of GitOps"
date: 2026-07-22
number: 333
description: "How to manage hundreds of ArgoCD applications without ever running kubectl apply again — using the App of Apps pattern."
---

You've probably heard the phrase "King of Kings" in movies and series. A ruler so powerful, other rulers bow to them.

Well, in the world of ArgoCD — meet the **App of Apps**. An application so powerful, it manages other applications.

Sounds fancy? Let me break it down.

## The Problem: kubectl apply is Not GitOps

If you're running ArgoCD, you're already doing GitOps for your actual workloads — your Helm charts, your Deployments, your Services. ArgoCD watches your Git repo and syncs everything automatically.

But here's the irony: how do you deploy the ArgoCD Application CRDs themselves?

```bash
kubectl apply -f app1-qc.yaml
kubectl apply -f app2-qc.yaml
kubectl apply -f another-app-uat.yaml
# ... repeat for every app, on every cluster, forever
```

Or manually click "New App" in the Argo UI, fill in the form, hit save. Same problem, different interface.

Every time a new service is onboarded, someone has to switch context to the cluster where ArgoCD is running and manually apply the manifest. That's not GitOps. That's just... work.

Now imagine you have **hundreds of apps** across **prod and nonprod clusters**. And one day your manager says:

> "Hey, we're migrating to a new cluster."

Or you need to roll out a configuration change across every app. Or a new environment spins up and every service needs a new Application manifest.

You're looking at updating and re-applying hundreds of YAML files manually. One by one. On multiple clusters. Without making a mistake.

That's the problem. The App of Apps is the solution.

Let me give you some real examples of what "hundreds of apps, one change" actually looks like:

**Your manager walks in and says "we're migrating from EKS to GKE"** — old approach: `kubectl get applications -n argocd`, export each one, re-apply them manually on the new GKE cluster, hope you didn't miss one. New approach: find-and-replace `destination.server` across all your YAML files with the new GKE API endpoint, open a PR, merge. ArgoCD points everything at the new cluster. Your manager is happy. You go home on time.

**Disable autosync across all prod apps overnight** — your team decides prod should require manual sync approvals going forward. Without App of Apps, someone is editing Application manifests in the cluster one by one at 11pm. With App of Apps, you open a PR, remove `automated:` from every YAML in `argo-apps-prod/`, merge. Done before the standup.

**Add `prune: true` to all nonprod apps** — the opposite. Nonprod environments are getting polluted with orphaned resources. Add `prune: true` to everything in `argo-apps-nonprod/` in one commit. Clean clusters from now on.

**Update `targetRevision` from `HEAD` to a specific tag across all prod apps** — your team wants prod pinned to `v2.4.1` instead of tracking HEAD. One sed command across the folder, one PR.

These are the changes that used to mean hours of careful, error-prone cluster access. With App of Apps they're a ten-second find-and-replace and a git push.

## What is App of Apps?

The App of Apps pattern is elegantly simple. An ArgoCD Application whose source points to a folder — and that folder contains other ArgoCD Application YAMLs.

```
app-of-apps/
├── argo-apps-prod/
│   ├── app1/
│   │   └── prod.yaml
│   └── app2/
│       └── prod.yaml
└── argo-apps-nonprod/
    ├── app1/
    │   ├── qc.yaml
    │   └── uat.yaml
    ├── app2/
    │   ├── qc.yaml
    │   └── uat.yaml
    └── new-app/
        └── qc.yaml
```

The parent Application watches this folder. When you drop a YAML in — ArgoCD creates the app. When you edit it — ArgoCD updates it. When you delete it — ArgoCD removes it.

Git is now the source of truth for your Application CRDs too. Not just your workloads.

## How It Works

### Step 1: Create the folder structure

In your git repo, create two folders — one per cluster:

```
app-of-apps/
├── argo-apps-prod/       ← apps for prod cluster
└── argo-apps-nonprod/    ← apps for nonprod cluster
```

### Step 2: Drop your Application YAMLs in

Each file is just a regular ArgoCD Application manifest:

```yaml
# argo-apps-nonprod/app1/qc.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: app1-qc
  namespace: argocd
spec:
  project: my-project
  source:
    repoURL: https://github.com/your-org/app1-cd.git
    path: helm
    targetRevision: HEAD
    helm:
      valueFiles:
        - values.qc.yaml
  destination:
    server: https://your-cluster-api-url.eks.amazonaws.com
    namespace: app1-qc
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

### Step 3: Create the parent Application (one-time bootstrap)

Most setups have a single ArgoCD instance managing all apps — all Applications live in the `argocd` namespace on that one cluster. In that case, you apply the parent just **once**, and ArgoCD takes it from there.

> If you have separate ArgoCD instances (e.g., one for prod, one for nonprod), you'd apply a parent on each. But for most teams — one apply, done.

```yaml
# parent.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: app-of-apps
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/your-org/your-cd-repo.git
    path: app-of-apps/argo-apps-nonprod
    targetRevision: HEAD
    directory:
      recurse: true    # picks up files in subfolders
  destination:
    server: https://kubernetes.default.svc
    namespace: argocd
  syncPolicy:
    automated:
      selfHeal: true
      prune: true
```

Apply it:

```bash
kubectl apply -f parent.yaml
```

That's it. From this point on, you never run `kubectl apply` again for app onboarding.

## Real World Scenarios

### Onboarding a new service

A new service called `new-app` is ready to go live in QC. You create:

```
argo-apps-nonprod/new-app/qc.yaml
```

Push to git. Within minutes, `new-app-qc` appears in the Argo UI — synced, healthy, managed. No one touched the cluster. No Slack message to the platform team saying "can you apply this manifest?" Just a git push.

### Cluster migration

Your team is migrating from an old EKS cluster to a new one. Old approach: `kubectl get applications -n argocd`, export each one, re-apply them manually on the new cluster, hope you didn't miss one.

New approach: update `destination.server` in your YAML files, open a PR, merge. ArgoCD points all your apps at the new cluster. And you have a git history proving exactly when and who made the change.

### Changing the target branch across all apps

Your team decides to pin all nonprod apps to a `develop` branch instead of tracking `HEAD`. Previously you'd have to edit every Application manifest in the cluster one by one.

Now a single find-and-replace across the folder, one commit, one push. Every app updated.

### Adding sync notifications to all prod apps

Your team wants email alerts whenever a prod app syncs. Add the annotation to your prod YAML files:

```yaml
metadata:
  annotations:
    notifications.argoproj.io/subscribe.on-sync-failed.email: platform@your-org.com
    notifications.argoproj.io/subscribe.on-sync-succeeded.email: platform@your-org.com
```

Push. Every prod app gets the notification config on next sync. No `kubectl edit`, no manual patching.

### Rolling out a new environment

Your team adds a new environment — `auat`. Every service needs a new Application pointing to `values.auat.yaml`. Copy, update the name and values file, drop in the folder:

```
argo-apps-nonprod/app1/auat.yaml
argo-apps-nonprod/app2/auat.yaml
argo-apps-nonprod/new-app/auat.yaml
```

Push once. All AUAT apps appear in Argo simultaneously.

### Decommissioning an app

`app2-qc` is being retired. Delete `argo-apps-nonprod/app2/qc.yaml` from git and push. ArgoCD removes the Application CRD — and with `prune: true` on the child app, it tears down the Deployments, Services, and Ingresses in the cluster too.

No orphaned resources. No forgotten namespaces. No "wait, is that app still running?" six months later.

## What Does It Look Like in the UI?

The parent `app-of-apps` shows up in the Argo UI like any other app. Click into it and instead of Pods and Deployments, you see your child Applications as its resources:

```
app-of-apps
├── app1-qc
├── app1-uat
├── app2-qc
├── new-app-qc
└── another-app-prod
```

Each child app is fully clickable — drill into it, see its own Deployments, Services, Pods, health status, and sync history. Everything works exactly the same as before, just with an extra layer of management on top.

## What Happens if the Parent Goes Down?

This is the most common concern people have. If the `app-of-apps` parent is deleted or ArgoCD restarts — do all the child apps disappear?

No. Child apps are independent Kubernetes resources. The parent creates them, but once they exist in the cluster, they run on their own. Deleting the parent doesn't cascade down and delete the children — it just means no one is watching the folder anymore.

Your workloads keep running. Your child apps keep syncing. The only thing you lose is the automated management of the Application CRDs themselves — until you re-apply the parent.

## Multi-Cluster From a Single Parent

Here's where it gets really powerful. The parent app lives on one cluster, but each child app can point to a completely different cluster via its `destination.server`:

```yaml
# argo-apps-nonprod/app1/qc.yaml  → deploys to QC cluster
destination:
  server: https://qc-cluster-api-url.eks.amazonaws.com

# argo-apps-nonprod/app1/uat.yaml → deploys to UAT cluster
destination:
  server: https://uat-cluster-api-url.eks.amazonaws.com

# argo-apps-prod/app1/prod.yaml   → deploys to prod cluster
destination:
  server: https://prod-cluster-api-url.eks.amazonaws.com
```

One parent. One git repo. Apps deployed across as many clusters as you need. The parent doesn't care where the child deploys — it just makes sure the Application CRD exists and is configured correctly.

## The Audit Trail You Never Had

Before App of Apps, if someone asked "when did `app2` get added to the QC cluster?" — good luck. It was a `kubectl apply` someone ran from their laptop six months ago. No record. No context. No idea.

With App of Apps, every change is a git commit:

- **Who** added a new app → git author
- **When** a branch was changed → commit timestamp
- **Why** an app was removed → commit message
- **What** the configuration looked like at any point in time → git history

For teams in regulated industries or with compliance requirements, this is significant. Your entire application lifecycle is now fully auditable — without any extra tooling.



If you already have hundreds of apps running in your cluster that were manually applied, don't worry. The parent only manages what it applies from git. ArgoCD uses tracking labels to know what it owns — your existing manually-applied apps have no such label, so the parent doesn't know they exist and won't touch them.

Migrate gradually: add apps to the folder one by one, and the parent adopts them. The rest stay untouched until you're ready.

## Conclusion

The App of Apps pattern closes the last GitOps gap — the Application CRDs themselves. Once the parent is bootstrapped (one `kubectl apply`, one time), your entire application lifecycle is managed through git.

Push to onboard. Edit to update. Delete to decommission.

No manual cluster access. No error-prone kubectl commands. No "who applied that?" questions in a post-incident review.

Just Git, ArgoCD, and peace of mind.

---

*Find more of my posts at [rajduwal.com.np/blog](https://rajduwal.com.np/blog). If you have any queries or just want to discuss how you're using it, drop me a mail at [root@rajduwal.com.np](mailto:root@rajduwal.com.np).*
