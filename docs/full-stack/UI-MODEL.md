# NOVA — User Interface (UI) Model

<!-- STATUS-BANNER -->
> **Status note (added in the 0.2 honesty pass).** This document is part
> of NOVA's *design record*. It was written in the aspirational voice of
> a finished 1.0 platform. **NOVA is a 0.2 research preview.** What is
> actually built and tested is a frontend type/effect/capability checker,
> a reference interpreter, a first-order native C backend, and the
> `regionlab` memory-model prototype. Everything here about a distributed
> runtime, a WASM UI layer, AI-agent governance, a package registry,
> self-hosting, or cross-language performance is **design, not
> implementation**. See [`README.md`](../../README.md),
> [`ROADMAP.md`](../../ROADMAP.md) and
> [`docs/known-issues.md`](../known-issues.md) for the real state.


**Status:** Production Design Reference  
**Cross-References:** [FULL-STACK-MODEL.md](FULL-STACK-MODEL.md), [SERVICE-MODEL.md](SERVICE-MODEL.md), [EFFECT-SYSTEM.md](../language/EFFECT-SYSTEM.md)

---

## 1. UI as Pure State Projections

In NOVA, a user interface component is not an opaque object with hidden lifecycle hooks. It is a **pure function** mapping application state and capability tokens to an immutable visual element tree:

$$\text{View} : (\text{State}, \text{ClientCaps}) \to \text{VNode}$$

```nova
struct UserProfileView {
    user: User,
    is_editing: Bool,
}

fn render_profile(view: UserProfileView) -> VNode {
    div(list![
        h1(view.user.name),
        p(view.user.email),
        if view.is_editing {
            button("Save", on_click(|| Msg::SaveClicked))
        } else {
            button("Edit", on_click(|| Msg::EditClicked))
        }
    ])
}
```

---

## 2. The Browser Capability Hierarchy

Browser APIs are strictly partitioned as unforgeable capability handles:

| Browser Capability | Permitted Actions | Prohibited Actions |
| :--- | :--- | :--- |
| **`dom: DOM`** | Update element nodes, read bounding rects | Cannot initiate network I/O |
| **`fetch: Fetch`** | HTTP/REST requests to allowed origins | Cannot mutate DOM or read cookies |
| **`storage: Storage`** | LocalStorage / IndexedDB persistence | Cannot open TCP sockets |
| **`history: History`** | Push/replace URL route states | Cannot execute arbitrary scripts |
| **`gpu: WebGPU`** | Dispatch compute & render shaders | Cannot read raw memory |

---

## 3. WebAssembly (WASM) & Fine-Grained Reactivity

NOVA compiles frontend components directly to WebAssembly:
1. **Zero Virtual DOM Overhead:** State changes trigger fine-grained node mutations directly via compiled WASM memory bindings.
2. **Hydration-Free Isomorphism:** The server renders the initial HTML snapshot; the client WASM bundle attaches directly to existing DOM nodes without re-rendering or running duplicate hydration passes.
3. **Deterministic Event Loop:** Messages are processed sequentially as pure transitions:
$$\text{Update} : (\text{Msg}, \text{State}) \to (\text{State}, \text{Cmd})$$
