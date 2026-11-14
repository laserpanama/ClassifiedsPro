import '@testing-library/jest-dom';

// jsdom does not implement ResizeObserver (needed by Radix UI primitives).
class ResizeObserverStub {
  observe() {}
  unobserve() {}
  disconnect() {}
}

if (typeof window !== 'undefined' && !window.ResizeObserver) {
  window.ResizeObserver = ResizeObserverStub;
}
