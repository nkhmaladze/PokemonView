import '@testing-library/jest-dom'

// jsdom 29 does not implement ResizeObserver, which Recharts'
// ResponsiveContainer requires (PriceHistoryChart.jsx, PRICE-07).
// Without this stub, every test that renders the chart throws a
// ReferenceError. observe() synchronously invokes the callback with a
// fixed content rect so ResponsiveContainer measures a non-zero size
// immediately in jsdom, instead of waiting on a real resize event that
// never fires in a test environment.
if (typeof globalThis.ResizeObserver === 'undefined') {
  class ResizeObserver {
    constructor(callback) {
      this.callback = callback
    }

    observe(target) {
      this.callback([{ target, contentRect: { width: 640, height: 280 } }])
    }

    unobserve() {}

    disconnect() {}
  }

  globalThis.ResizeObserver = ResizeObserver
}
