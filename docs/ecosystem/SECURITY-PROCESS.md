# NOVA — Security Process & Vulnerability Disclosure

**Status:** Official Security Policy  
**Cross-References:** [SECURITY-MODEL.md](../language/SECURITY-MODEL.md), [AI-SECURITY.md](../ai/AI-SECURITY.md), [RELEASE-PROCESS.md](RELEASE-PROCESS.md)

---

## 1. Coordinated Vulnerability Disclosure Policy

The NOVA core team is committed to maintaining the highest security standards across the compiler, runtime, capability sandboxes, and package ecosystem.

If you discover a security vulnerability (such as a memory safety bypass in Region XOR, a capability sandbox escape, or a compiler type-soundness hole), please disclose it privately via:

$$\textbf{Email: } \texttt{security@ieeecsopen.org}$$

---

## 2. Vulnerability Response Timeline

| Milestone | Target Response Window | Action Taken |
| :--- | :--- | :--- |
| **Initial Acknowledgment** | Within **48 hours** | Triage report and vulnerability confirmation. |
| **Patch & Verification** | Within **14 days** | Core security team develops and tests isolated fix. |
| **Security Release** | Point Release (e.g. 1.0.1) | Critical patch deployed across Stable and Beta channels. |
| **Public Disclosure** | **90 days** post-patch | Full CVE write-up published with root-cause analysis. |

---

## 3. Severity Classification

1. **Critical:** Arbitrary memory corruption, capability sandbox escape, or remote code execution without `! {Unsafe}` capability.
2. **High:** Type-soundness hole allowing un-annotated capability capture.
3. **Medium:** Denial-of-service in compiler or local resource budget escape.
4. **Low:** Minor telemetry or diagnostic informational leak.
