# React Testing Library (RTL)

> [!NOTE]   
> **Status**: In Progress

---

## What is RTL?

React Testing Library is a lightweight testing utility built on top of the DOM Testing Library. It encourages testing components the way users interact with them — by querying the DOM rather than component internals.

> "The more your tests resemble the way your software is used, the more confidence they can give you." — Kent C. Dodds

---

## Installation

```bash
npm install -D @testing-library/react @testing-library/jest-dom @testing-library/user-event
```

### Setup File (jest.setup.js or vitest.setup.ts)

```javascript
import '@testing-library/jest-dom';
```

---

## Core API

### render

Renders a component into a virtual DOM for testing.

```javascript
import { render } from '@testing-library/react';
import MyComponent from './MyComponent';

const { getByText, getByRole } = render(<MyComponent />);
```

---

## Query Types

Queries follow the pattern: `getBy`, `queryBy`, `findBy` (async), and their `AllBy` variants.

| Prefix | Throws if not found | Returns null if not found | Async |
|---|---|---|---|
| `getBy` | Yes | No | No |
| `queryBy` | No | Yes | No |
| `findBy` | Yes | No | Yes (Promise) |

### Query Selectors (in order of preference)

```javascript
getByRole('button', { name: /submit/i })   // Preferred
getByLabelText('Email')                     // Form inputs
getByPlaceholderText('Search...')
getByText('Hello World')
getByDisplayValue('selected option')
getByAltText('profile picture')
getByTitle('close')
getByTestId('my-element')                   // Last resort
```

---

## user-event (Simulating User Interactions)

`@testing-library/user-event` provides more realistic user interactions than `fireEvent`.

```javascript
import userEvent from '@testing-library/user-event';

const user = userEvent.setup();

await user.click(button);
await user.type(input, 'hello');
await user.clear(input);
await user.selectOptions(select, 'option-value');
await user.keyboard('{Enter}');
await user.tab();
```

---

## Complete Example

```javascript
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import LoginForm from './LoginForm';

describe('LoginForm', () => {
  it('submits the form with user credentials', async () => {
    const handleSubmit = jest.fn();
    const user = userEvent.setup();

    render(<LoginForm onSubmit={handleSubmit} />);

    await user.type(screen.getByLabelText('Email'), 'user@example.com');
    await user.type(screen.getByLabelText('Password'), 'secret');
    await user.click(screen.getByRole('button', { name: /login/i }));

    expect(handleSubmit).toHaveBeenCalledWith({
      email: 'user@example.com',
      password: 'secret',
    });
  });

  it('shows an error when fields are empty', async () => {
    const user = userEvent.setup();

    render(<LoginForm />);

    await user.click(screen.getByRole('button', { name: /login/i }));

    expect(screen.getByText(/email is required/i)).toBeInTheDocument();
  });
});
```
---

## jest-dom Custom Matchers

```javascript
    expect(element).toBeInTheDocument();
    expect(element).toBeVisible();
    expect(element).toBeDisabled();
    expect(element).toBeEnabled();
    expect(element).toHaveTextContent('Hello');
    expect(element).toHaveValue('input value');
    expect(element).toHaveClass('active');
    expect(element).toHaveAttribute('href', '/home');
    expect(element).toBeChecked();
    expect(element).toHaveFocus();
```

---

## Testing Async Components

```javascript
import { render, screen, waitFor } from '@testing-library/react';

it('loads and displays users', async () => {
  render(<UserList />);

  // findBy* queries automatically wait for the element
  const user = await screen.findByText('Alice');
  expect(user).toBeInTheDocument();

  // Or use waitFor for more complex assertions
  await waitFor(() => {
    expect(screen.getByText('Alice')).toBeInTheDocument();
  });
});
```