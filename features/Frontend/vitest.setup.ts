// Test setup file for Vitest
import { vi } from 'vitest';

// Mock window and document for browser APIs
Object.defineProperty(window, 'location', {
  value: {
    pathname: '/',
    href: 'http://localhost:3000',
  },
  writable: true,
});

// Mock localStorage
Object.defineProperty(window, 'localStorage', {
  value: {
    getItem: vi.fn(),
    setItem: vi.fn(),
    removeItem: vi.fn(),
    clear: vi.fn(),
  },
  writable: true,
});

// Mock fetch API
global.fetch = vi.fn();

// Mock console methods to reduce test noise
global.console = {
  ...console,
  log: vi.fn(),
  error: vi.fn(),
  warn: vi.fn(),
  info: vi.fn(),
  debug: vi.fn(),
};

export {};