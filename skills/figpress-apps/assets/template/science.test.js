// Run with: uv run figpress-apps test webapps/NAME
// Check the JS against numbers computed by the paper's Python (paste them in, or export them).
import { test } from "node:test";
import assert from "node:assert/strict";
import { project } from "app/science.js";

test("viewing along +z keeps x and y", () => {
  const { xy } = project(new Float64Array([1, 2, 3, -4, 5, 6]), [0, 0, 1]);
  assert.deepEqual(Array.from(xy), [1, 2, -4, 5]);
});
