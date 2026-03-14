# Change: Validate incompatible fields in CategoryCollection*Args models

## Why
`CategoryCollectionAddArgs`, `CategoryCollectionChangeArgs`, and `CategoryCollectionUpdateArgs` accept fields that only apply to one type (`category` or `collection`). Passing incompatible fields (e.g. `categories` with `type='category'`) is silently ignored, giving callers no feedback.

## What Changes
- Add `model_validator(mode='after')` to `CategoryCollectionAddArgs` — reject `categories` when `type='category'`; reject `dir`/`patterns` when `type='collection'`
- Add `model_validator(mode='after')` to `CategoryCollectionChangeArgs` — reject `new_categories` when `type='category'`; reject `new_dir`/`new_patterns` when `type='collection'`
- Add `model_validator(mode='after')` to `CategoryCollectionUpdateArgs` — reject `add_categories`/`remove_categories` when `type='category'`; reject `add_patterns`/`remove_patterns` when `type='collection'`

## Impact
- Affected specs: `tool-infrastructure`
- Affected code: `src/mcp_guide/tools/tool_category.py`
