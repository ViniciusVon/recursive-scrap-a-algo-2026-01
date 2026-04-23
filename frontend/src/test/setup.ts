/**
 * Setup global dos testes.
 *
 * Plugga os matchers do `@testing-library/jest-dom` no `expect` do
 * Vitest (ex.: `toBeInTheDocument`). Outros ajustes por-teste ficam no
 * próprio arquivo (fake timers, mocks, etc.).
 */

import '@testing-library/jest-dom/vitest';
