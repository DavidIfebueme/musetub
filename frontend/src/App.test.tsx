import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';

import App from './App';

describe('App', () => {
  it('shows login heading when logged out', () => {
    localStorage.removeItem('musetub_token');
    render(<App />);
    expect(screen.getByText('MuseTub')).toBeInTheDocument();
  });
});
