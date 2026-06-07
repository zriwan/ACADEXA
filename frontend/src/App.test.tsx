import React from 'react';
import { render, screen } from '@testing-library/react';

// Prevent importing the real API client (which pulls in ESM axios) during tests
jest.mock('./api/client', () => ({
  api: { get: jest.fn(() => Promise.resolve({ data: null })) },
  setAuthToken: jest.fn(),
}));

import App from './App';

test('renders app loading state', async () => {
  render(<App />);
  expect(await screen.findByText(/welcome to acadexa/i)).toBeInTheDocument();
  expect(screen.getByLabelText(/email address/i)).toBeInTheDocument();
  expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
});
