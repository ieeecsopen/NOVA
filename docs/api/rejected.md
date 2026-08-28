# Module `rejected.nova`

*Source file: `examples/module-system/rejected.nova`*

---

> *Warning: Could not extract full type information: error[E0120]: `validate` is private to module `geometry`
  --> examples/module-system/rejected.nova:12:5
   |
12 |     validate(Rectangle { width: 1, height: 1 })
   |     ^^^^^^^^ not accessible from here
  = help: mark it `pub` in `geometry`*