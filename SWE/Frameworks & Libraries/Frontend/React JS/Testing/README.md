# React Testing

> [!NOTE]   
> **Status**: In Progress

---

## Overview

Testing in React ensures components behave correctly and helps prevent regressions. The React ecosystem has several well-established tools, each targeting different layers of the testing pyramid.

---

## Testing Pyramid

Unit Tests → Integration Tests → End-to-End (E2E) Tests

- **Unit Tests** – Test individual functions or components in isolation
- **Integration Tests** – Test how multiple components work together
- **E2E Tests** – Simulate real user flows through the entire application

---

## Tools in This Directory

| Tool | Type | Best Used For |
|---|---|---|
| [Jest](./Jest.md) | Unit / Integration | Test runner, assertions, mocking |
| [React Testing Library](./React-Testing-Library.md) | Unit / Integration | Component rendering and user interaction |
| [Vitest](./Vitest.md) | Unit / Integration | Jest-compatible runner for Vite projects |
| [Cypress](./Cypress.md) | E2E / Integration | Full browser-based user flow testing |

---

## Common Testing Concepts

### Arrange, Act, Assert (AAA)
The standard pattern for structuring tests:
1. **Arrange** – Set up the component/data
2. **Act** – Trigger an action or event
3. **Assert** – Verify the expected outcome

### Test File Conventions
- Place test files alongside components: `Button.test.tsx`
- Or in a `__tests__` folder: `__tests__/Button.test.tsx`
- Test files match the pattern: `*.test.ts`, `*.test.tsx`, `*.spec.ts`

### Mocking
Mocking replaces real dependencies (APIs, modules, timers) with controlled fake versions to isolate the unit under test.

---

## Quick Setup (Vite + React)

```bash
# Using Vitest (recommended for Vite projects)
npm install -D vitest @testing-library/react @testing-library/jest-dom @testing-library/user-event jsdom

# Using Jest (CRA or custom setup)
npm install -D jest @testing-library/react @testing-library/jest-dom @testing-library/user-event babel-jest
```