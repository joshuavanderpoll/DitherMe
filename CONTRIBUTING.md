# Contributing to DitherMe

Thanks for taking the time to contribute. This guide covers how to set up the project, the commit conventions we use, and how to open a pull request.

## Getting started

You need Rust, Node.js, pnpm, and the [Tauri prerequisites](https://tauri.app/start/prerequisites/) for your OS.

```bash
git clone https://github.com/joshuavanderpoll/DitherMe.git
cd DitherMe
pnpm install
pnpm tauri dev
```

The layout:

- `crates/dither_core` - the Rust image pipeline and dithering algorithms, no UI.
- `src-tauri` - the Tauri shell and commands.
- `src` - the Svelte and TypeScript UI.

## Before you open a pull request

Run these and make sure they pass:

```bash
cargo test -p dither_core     # core pipeline tests
cargo fmt --all               # format Rust
cargo clippy --all-targets    # lint Rust
pnpm check                    # type-check the frontend
```

If you change the pipeline or an algorithm, add or update a test in `crates/dither_core`.

## Commit messages

We use [Conventional Commits](https://www.conventionalcommits.org/). Format:

```
<type>(<scope>): <short summary>
```

Types:

- `feat` - a new feature
- `fix` - a bug fix
- `docs` - documentation only
- `style` - formatting, no code change
- `refactor` - code change that is neither a fix nor a feature
- `perf` - performance improvement
- `test` - adding or fixing tests
- `build` - build system or dependencies
- `ci` - CI configuration
- `chore` - anything else

Scope is optional but preferred. Common scopes: `core`, `ui`, `tauri`, `algorithms`, `ci`.

Examples:

```
feat(ui): add before/after split view
fix(core): realign alpha after pixelation
perf(core): optimize dev build to opt-level 3
docs: update build instructions
```

Keep the summary under ~72 characters, imperative mood ("add" not "added"). Put the why in the body when it isn't obvious.

## Pull requests

- Branch off `main` (or the active feature branch).
- Keep PRs focused; smaller is easier to review.
- Describe what changed and why. Link related issues.
- Make sure the checks above pass.

## Reporting bugs

Open an issue using the bug report template. Include your OS and the output of `rustc --version`, `node --version`, and `pnpm --version`.
