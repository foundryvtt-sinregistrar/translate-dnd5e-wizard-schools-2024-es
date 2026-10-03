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
  if (!Array.isArray(source) || !translation) return source;
  return source.map(advancement => translation[advancement._id] ? merge(clone(advancement), translation[advancement._id]) : advancement);
}

Hooks.once("babele.init", babele => {
  if (!babele?.registerConverters) return;
  Hooks.once("setup", () => {
    if (game.settings.get("core", "language")?.split("-")[0]?.toLowerCase() !== "es") return;
    babele.registerConverters({ wizardSchoolsActivitiesById, wizardSchoolsEffectsById, wizardSchoolsAdvancementById });
  });
});
