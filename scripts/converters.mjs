const clone = value => globalThis.foundry?.utils?.deepClone ? foundry.utils.deepClone(value) : structuredClone(value);
const merge = (target, patch) => {
  if (globalThis.foundry?.utils?.mergeObject) return foundry.utils.mergeObject(target, patch, { insertKeys: true, overwrite: true, inplace: true });
  return Object.assign(target, patch);
};

export function wizardSchoolsActivitiesById(source, translation) {
  if (!source || !translation) return source;
  const result = clone(source);
  for (const [id, activity] of Object.entries(result)) if (translation[id]) merge(activity, translation[id]);
  return result;
}

export function wizardSchoolsEffectsById(source, translation) {
  if (!Array.isArray(source) || !translation) return source;
  return source.map(effect => translation[effect._id] ? merge(clone(effect), translation[effect._id]) : effect);
}

export function wizardSchoolsAdvancementById(source, translation) {
  if (!source || typeof source !== "object" || !translation || typeof translation !== "object") return source;
  const result = clone(source);
  const patches = Array.isArray(translation)
    ? Object.fromEntries(translation.filter(value => value?._id ?? value?.id).map(value => [value._id ?? value.id, value]))
    : translation;
  const rows = Array.isArray(result.contents) ? result.contents : result;
  for (const [key, advancement] of Object.entries(rows)) {
    if (!advancement || typeof advancement !== "object" || Array.isArray(advancement)) continue;
    const id = advancement._id ?? advancement.id ?? key;
    const patch = Object.hasOwn(patches, id) ? patches[id] : undefined;
    if (!patch || typeof patch !== "object" || Array.isArray(patch)) continue;
    const label = typeof patch.name === "string" ? patch.name : patch.title;
    if (typeof label === "string") advancement["name" in advancement ? "name" : "title"] = label;
    if (typeof patch.hint === "string") advancement.hint = patch.hint;
  }
  return result;
}

Hooks.once("babele.init", babele => {
  if (!babele?.registerConverters) return;
  Hooks.once("setup", () => {
    if (game.settings.get("core", "language")?.split("-")[0]?.toLowerCase() !== "es") return;
    babele.registerConverters({ wizardSchoolsActivitiesById, wizardSchoolsEffectsById, wizardSchoolsAdvancementById });
  });
});
