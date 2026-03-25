# Jest

> [!NOTE]   
> **Status**: In Progress

---

## What is Jest?

Jest is a JavaScript testing framework developed by Meta. It is the most widely used test runner in the React ecosystem and works out of the box with Create React App (CRA).

---

## Key Features

- Zero-config setup with CRA
- Built-in test runner, assertion library, and mock system
- Snapshot testing
- Code coverage reporting
- Parallel test execution

---

## Installation

```bash
npm install -D jest babel-jest @babel/core @babel/preset-env @babel/preset-react
```

For TypeScript:
```bash
npm install -D ts-jest @types/jest
```

---

## Configuration (jest.config.js)

```javascript
module.exports = {
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  transform: {
    '^.+\\.(ts|tsx)$': 'ts-jest',
  },
};
```

---

## Core Concepts

### describe / it / test

```javascript
describe('MyComponent', () => {
  it('renders correctly', () => {
    // test body
  });

  test('handles click events', () => {
    // test body
  });
});
```

### Matchers (expect)

```javascript
expect(value).toBe(42);               // strict equality
expect(value).toEqual({ a: 1 });      // deep equality
expect(value).toBeTruthy();
expect(value).toBeFalsy();
expect(value).toContain('hello');
expect(fn).toThrow();
expect(fn).toHaveBeenCalled();
expect(fn).toHaveBeenCalledWith('arg');
```

### Mocking

```javascript
// Mock a function
const mockFn = jest.fn();
mockFn.mockReturnValue(42);
mockFn.mockResolvedValue({ data: 'ok' }); // async

// Mock a module
jest.mock('./api', () => ({
  fetchUser: jest.fn().mockResolvedValue({ name: 'Alice' }),
}));

// Spy on a method
const spy = jest.spyOn(object, 'method');
```

### beforeEach / afterEach / beforeAll / afterAll

```javascript
beforeEach(() => {
  // Runs before each test
});

afterEach(() => {
  jest.clearAllMocks(); // Clean up mocks
});

beforeAll(() => {
  // Runs once before all tests
});

afterAll(() => {
  // Runs once after all tests
});
```

---

## Snapshot Testing

```javascript
import { render } from '@testing-library/react';
import Button from './Button';

test('matches snapshot', () => {
    const { asFragment } = render(<Button label="Click me" />);
    expect(asFragment()).toMatchSnapshot();
});
```

> Snapshots are stored in `__snapshots__/` and should be committed to version control. Update with `jest --updateSnapshot`.

---

## Running Tests

```bash
npx jest                  # Run all tests
npx jest --watch          # Watch mode
npx jest --coverage       # With coverage report
npx jest Button           # Run tests matching "Button"
```