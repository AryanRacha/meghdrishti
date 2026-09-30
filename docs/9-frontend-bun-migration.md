# 9 - Frontend Bun Migration

## Objective
Port the `frontend/` application from npm to Bun (v1.4+) for faster package installation, native script execution, and reduced dependency footprint.

## Changes Made
1. **Package Management**:
   - Removed `package-lock.json`.
   - Generated `bun.lock`.
   - Added `@types/bun` to `devDependencies`.
2. **Build and Verification**:
   - `bun install`: Clean package installation with zero conflicts.
   - `bun run build`: TypeScript compilation (`tsc -b`) and Vite production bundling (`dist/` output: ~434 kB JS, ~58 kB CSS).
   - `bun run lint`: Oxlint fast linting passed with 0 errors and 0 warnings across 31 files in ~50 ms.
   - `bun run dev`: Vite dev server starts with HMR on `http://localhost:5173/`.

## Execution Commands
```bash
cd frontend
bun install
bun run dev      # Launch Meghdrishti dev server
bun run build    # Type-check and build for production
bun run lint     # Fast Oxlint validation
```
