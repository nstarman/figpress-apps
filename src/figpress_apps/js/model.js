// A standalone model with the anywidget model API, so components run the same on a web page
// and in a notebook. Change detection is by identity: replace values, never mutate them.

export function createModel(initial = {}) {
  const state = new Map(Object.entries(initial));
  const listeners = new Map(); // event → Set(fn)
  return {
    get: (key) => state.get(key),
    set(key, value) {
      if (state.get(key) === value) return;
      state.set(key, value);
      for (const fn of [...(listeners.get(`change:${key}`) ?? [])]) fn();
    },
    on(event, fn) {
      if (!listeners.has(event)) listeners.set(event, new Set());
      listeners.get(event).add(fn);
    },
    off(event, fn) {
      if (event === undefined) listeners.clear();
      else if (fn === undefined) listeners.delete(event);
      else listeners.get(event)?.delete(fn);
    },
    save_changes() {}, // nothing to sync on a web page
    send() {},
  };
}
