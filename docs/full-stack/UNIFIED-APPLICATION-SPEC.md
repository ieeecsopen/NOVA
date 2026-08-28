# NOVA — Unified Application Specification

**Status:** Production Design Reference  
**Cross-References:** [PLATFORM-MODEL.md](../distributed/PLATFORM-MODEL.md), [END-TO-END-ARCHITECTURE.md](END-TO-END-ARCHITECTURE.md), [APPLICATION-MODEL.md](APPLICATION-MODEL.md), [DATA-MODEL.md](DATA-MODEL.md)

---

## 1. Whole-Application Topology Block

```nova
application CampusPlatform {

    // 1. Shared Domain Entities & Contracts
    entities {
        struct Student {
            id: UUID,
            name: String,
            email: String,
            credits: Int,
        }
        invariant credits >= 0;

        struct CampusEvent {
            id: UUID,
            title: String,
            capacity: Int,
            enrolled: Int,
        }
        invariant enrolled <= capacity;
    }

    // 2. Client Frontend (Compiled to WASM & SSR HTML)
    frontend WebPortal {
        entry: pages.Dashboard,
        allowed_capabilities: [DOM, Fetch, LocalStorage],
    }

    // 3. Backend RPC Services & Background Workers
    services {
        CampusAPI {
            routes: api.Routes,
            requires: [Database, Secret, Clock],
        }

        NotificationWorker {
            tasks: jobs.EmailQueue,
            requires: [Network, Database],
        }
    }

    // 4. Autonomous AI Agents
    agents {
        StudyAssistant {
            model: Model::Reasoning("claude-3-7-sonnet"),
            capabilities: [Database.read],
            budget: {
                tokens < 15000,
                cost < 0.05,
                time < 20000,
            },
        }
    }

    // 5. Database Storage & Relational Mappings
    database Postgres {
        entities: [Student, CampusEvent],
        pool_size: 25,
    }

    // 6. Deployment Synthesis Target
    deployment {
        target: Container,
        replicas: 3,
        resources: {
            memory: "512MB",
            cpu: "1.0",
        },
    }
}
```

---

## 2. Compile-Time Application Invariants

Before emitting executables or deployment bundles, the compiler establishes:
1. **Tier Capability Isolation:** `frontend WebPortal` cannot hold references to `Database` or `Secret` handles.
2. **Schema Uniformity:** Entity structures match database table column types with mathematical precision.
3. **Agent Resource Ceiling:** AI assistant agents are guaranteed to terminate within their declared `budget {}` bounds.
