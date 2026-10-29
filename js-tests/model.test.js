import { test } from "node:test";
import assert from "node:assert/strict";
import { createModel } from "figpress-apps/model.js";

test("get/set and change events by identity", () => {
  const m = createModel({ a: 1 });
  assert.equal(m.get("a"), 1);
  const calls = [];
  const fn = (...args) => calls.push(args);
  m.on("change:views", fn);
  const v = { x: [1, 0, 0] };
  m.set("views", v);
  m.set("views", v); // same object: no event
  m.set("views", { ...v });
  assert.equal(calls.length, 2);
  assert.deepEqual(calls[0], []); // AFM: callbacks get no arguments
  assert.equal(m.get("missing"), undefined);
});

test("off removes listeners; save_changes is a no-op", () => {
  const m = createModel();
  let n = 0;
  const f = () => n++, g = () => n++;
  m.on("change:a", f); m.on("change:a", g); m.on("change:b", f);
  m.off("change:a", f); m.set("a", 1); assert.equal(n, 1);
  m.off("change:a"); m.set("a", 2); assert.equal(n, 1);
  m.off(); m.set("b", 1); assert.equal(n, 1);
  m.save_changes();
});
