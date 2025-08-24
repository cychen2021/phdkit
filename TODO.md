# TODOs of phdkit

- [ ] Design the `configlib` module for functions a la classes
- [ ] Figure out how to strictly separate `load_config` and `load_env` for `configurable` classes
- [ ] 🏃Simplify the usage pattern of `load_config` and `load_env`
- [ ] Consider how to handle configurations of base classes in `configlib`
- [ ] Add error messages if using a configuration setting before it is loaded
- [ ] Consider how to use `configlib` for the context manager protocol
- [x] Explore how to handle optional settings in `configlib`
- [ ] Add docs for default setting values in `configlib`
- [ ] Implement `log.watchdog`
- [x] Implement the `subshell` functionality of the `rich` wrapper module
- ~~[ ] Implement the `dyntqdm` functionality of the `rich` wrapper module~~ Already support by `rich`
- [ ] Make `infix_fn` type-safe
- [ ] Add a py-tree-sitter wrapper module
