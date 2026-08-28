# NOVA — Autonomous Agent Model

**Status:** Production Design Reference  
**Cross-References:** [AI-MODEL.md](AI-MODEL.md), [AI-SECURITY.md](AI-SECURITY.md), [COST-MODEL.md](COST-MODEL.md), [CAPABILITY-MODEL.md](CAPABILITY-MODEL.md)

---

## 1. The Cardinal Principle of Agent Safety

> **An AI agent possesses ZERO implicit authority.**  
> Every action the agent performs must pass through NOVA's capability and effect system.

An agent in NOVA is not a magical autonomous entity with ambient system access; it is an **attenuated state machine** operating under strict resource and capability bounds.

```nova
agent Researcher {
    model: Model::Reasoning("claude-3-7-sonnet@20260219"),

    // Explicitly delegated capabilities ONLY
    capabilities: {
        web: Network,
        db: Database,
    },

    // Strict resource envelope
    budget: {
        tokens < 20000,
        time < 30000,      // 30 seconds max
        cost < 0.10,       // $0.10 max expenditure
        iterations < 8,    // Max 8 reasoning cycles
    },
}
```

---

## 2. Tools as Capability-Protected Functions

In NOVA, an agent tool is simply an ordinary typed function requiring specific capability arguments. An agent **cannot invoke a tool if it does not hold the capability**:

```nova
// Tool requiring Network capability
fn search_web(net: Network, query: String) -> Result[List[String], Error] ! {Network} {
    net.get(format("https://search.internal?q={}", query))
}

// Tool requiring Database capability
fn read_documents(db: Database, user_id: UUID) -> Result[List[Doc], Error] ! {Database} {
    db.query("SELECT * FROM documents WHERE user_id = ?", user_id)
}
```

If an attacker injects a prompt asking the agent to delete files (`Filesystem`), the request is physically impossible: the `Researcher` agent holds no `Filesystem` capability handle, and the compiler rejects the operation statically.

---

## 3. Human-in-the-Loop Approval Gates

Privileged mutations require an **unforgeable human approval token**:

```nova
struct ApprovalToken[Action] {
    action: Action,
    approved_by: UserID,
    timestamp: Int,
}

fn execute_wire_transfer(vault: Secret, approval: ApprovalToken[TransferAction], amount: Int) -> Result[Receipt, Error] ! {Secret} {
    // Only executes if unforgeable approval capability is held!
    vault.sign_transfer(amount)
}
```
