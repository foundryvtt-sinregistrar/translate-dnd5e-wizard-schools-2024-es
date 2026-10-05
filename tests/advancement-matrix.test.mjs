import assert from "node:assert/strict";
import { test } from "node:test";
globalThis.Hooks = { once() {} };
globalThis.foundry = { utils: { deepClone: structuredClone } };
const { wizardSchoolsAdvancementById: convert } = await import("../scripts/converters.mjs");

for (const format of ["array", "indexed", "contents"]) {
  test(`advancement matrix: ${format}`, () => {
    const row = { _id: "advance000000001", name: "Feature", hint: "Hint", level: 3, configuration: { pool: ["uuid"] }, value: { chosen: 1 } };
    const source = format === "array" ? [row] : format === "contents" ? { contents: [row], metadata: { count: 1 } } : { originalKey: row };
    const before = structuredClone(source);
    for (const labelKey of ["name", "title"]) {
      const result = convert(source, { [row._id]: { [labelKey]: "Rasgo", hint: "Pista", level: 20, configuration: {}, value: {} } });
      const expected = structuredClone(source);
      const target = format === "array" ? expected[0] : format === "contents" ? expected.contents[0] : expected.originalKey;
      target.name = "Rasgo";
      target.hint = "Pista";
      assert.deepEqual(result, expected);
      assert.notEqual(result, source);
      assert.deepEqual(source, before);
    }
    assert.equal(convert(source, undefined), source);
    assert.deepEqual(convert(source, {}), source);
  });
}
test("indexed key can identify an advancement without an embedded ID", () => {
  assert.deepEqual(convert({ key: { title: "Feature", level: 3 } }, { key: { title: "Rasgo" } }), { key: { title: "Rasgo", level: 3 } });
});
