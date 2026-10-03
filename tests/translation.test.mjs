import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";

const translation = JSON.parse(readFileSync(new URL("../compendium/dnd5e-2024-wizard-schools.classes24.json", import.meta.url), "utf8"));
const registration = readFileSync(new URL("../scripts/babele-register.mjs", import.meta.url), "utf8");

test("registers Babele with the current module ID", () => {
  assert.match(registration, /module: "translate-dnd5e-wizard-schools-2024-es"/);
});

test("Spanish translation has a stable Babele schema", () => {
  assert.equal(translation.metadata.pack, "dnd5e-2024-wizard-schools.classes24");
  assert.equal(translation.metadata.entries, 24);
  assert.equal(Object.keys(translation.entries).length, 24);
  assert.equal(Object.keys(translation.folders).length, 4);
  for (const [id, entry] of Object.entries(translation.entries)) {
    assert.match(id, /^[A-Za-z0-9]{16}$/);
    assert.equal(typeof entry.name, "string");
    assert.equal(typeof entry.description, "string");
  }
});
