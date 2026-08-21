INDEX_CODE = """for relpath in sorted(files):
    result = self._module_parser.parse(relpath, files[relpath], project_modules)
    modules[result.module.fqn] = result.module
    source_roots |= result.source_roots
    for analysis in result.classes:
        classes[analysis.record.fqn] = analysis.record
        all_analyses.append(analysis)
    for record in result.functions:
        functions[record.fqn] = record"""

RESOLVE_CODE = """self_types = SelfExprTypeResolver(record.cls, self._self_resolver, self._index)
local_bindings = dict(module_bindings.get(record.module, {}))
local_bindings.update(self._param_bindings(record))
local_bindings.update(self._local_binder.collect(record.body, scope, self_types))
resolver = CallTargetResolver(
    record, scope, local_bindings, self._attribute_path, self._self_resolver,
    self._unique_names, self.tier_counter, self._index,
)"""

JUDGE_CODE = """for start in range(0, len(representatives), _BATCH_SIZE):
    batch = representatives[start : start + _BATCH_SIZE]
    batch_verdicts = self._judge_batch(batch)
    for candidate in batch:
        fingerprint = fingerprints[candidate.site_id]
        verdict = batch_verdicts[candidate.site_id]
        self._cache.put(fingerprint, verdict)
        for duplicate in groups[fingerprint]:
            results[duplicate.site_id] = verdict
self._cache.flush()
return results"""
