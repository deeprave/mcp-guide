## 1. FeatureValue abstraction

- [x] 1.1 Design and introduce a real runtime `FeatureValue` abstraction
- [x] 1.2 Support construction from all currently valid raw flag shapes
- [x] 1.3 Add explicit raw serialization and display-formatting helpers
- [x] 1.4 Add tests for construction, normalization, and raw round-tripping

## 2. Flag pipeline integration

- [x] 2.1 Update validators and normalizers to work with the new abstraction
- [x] 2.2 Update project/global flag storage layers to wrap and unwrap values explicitly
- [x] 2.3 Update flag resolution helpers to return and merge the new abstraction consistently
- [x] 2.4 Add tests for project/global/resolved flag compatibility

## 3. Model and rendering integration

- [x] 3.1 Update config and project models to store or expose feature values through the new abstraction safely
- [x] 3.2 Update display-oriented rendering code to use `FeatureValue` display helpers
- [x] 3.3 Add tests for rendered flag output using the new abstraction

## 4. Tool integration

- [x] 4.1 Update feature-flag tools and any other affected tool responses to use explicit raw/display conversions
- [x] 4.2 Add tests for unchanged user-facing flag input and output behavior

## 5. Validation

- [x] 5.1 Run focused feature-flag, model, rendering, and tool tests for the touched behavior
- [x] 5.2 Run `openspec validate refactor-featurevalue --strict`
