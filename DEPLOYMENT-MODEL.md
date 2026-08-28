# NOVA — Application Deployment Model

**Status:** Production Design Reference  
**Cross-References:** [APPLICATION-MODEL.md](APPLICATION-MODEL.md), [ECOSYSTEM-DESIGN.md](ECOSYSTEM-DESIGN.md), [REPRODUCIBILITY-MODEL.md](REPRODUCIBILITY-MODEL.md)

---

## 1. Intermediate Deployment Representation

NOVA rejects coupling language syntax directly to ephemeral cloud orchestrators (e.g. Kubernetes, Helm, Terraform). 

Instead, the language compiles whole-system `application` topology definitions into an **Intermediate Deployment Model (IDM)**:

```
[application CampusPortal { ... }] 
                 │
                 ▼
[Intermediate Deployment Model (IDM)]
                 │
     +-----------+-----------+-----------+
     |                       |           |
     v                       v           v
[OCI Container Images]   [Edge WASM]   [Native Monolith]
```

---

## 2. Supported Deployment Targets

```bash
# 1. Deploy as OCI Container Bundle
nova deploy --target container -o dist/docker/

# 2. Deploy as Serverless Edge WASM Bundle (Cloudflare/Fastly)
nova deploy --target edge -o dist/edge/

# 3. Deploy as Bare-Metal Systemd Monolith
nova deploy --target monolith -o dist/bin/
```

---

## 3. Boundary & Security Synthesis

When synthesizing deployment targets, the deployment compiler automatically generates:
1. **Least-Privilege Security Profiles:** Configures Linux seccomp and capability filters based exactly on the service's declared NOVA capabilities.
2. **Network Policy Firewalls:** Generates ingress/egress firewall rules allowing network communication only along explicit channel topologies.
3. **Database Migration Hooks:** Bundles verified SQL DDL migrations with automated rollback scripts.
