## 1. Analysis and Design
- [x] 1.1 Review current WorkflowState data structure and comparison needs
- [x] 1.2 Design change detection data structures (ChangeType enum, ChangeEvent class)
- [x] 1.3 Define semantic comparison functions for each workflow field
- [x] 1.4 Plan template instruction appending mechanism

## 2. Core Change Detection Logic
- [x] 2.1 Create ChangeType enum (PHASE, ISSUE, TRACKING, DESCRIPTION, QUEUE)
- [x] 2.2 Create ChangeEvent data class with from/to values
- [x] 2.3 Implement detect_workflow_changes(old_state, new_state) function
- [x] 2.4 Implement individual field comparison functions (compare_phase, compare_issue, etc.)
- [x] 2.5 Handle startup case (old_state is None) gracefully

## 3. Template System Integration
- [x] 3.1 Create phase-transition instruction generation using existing phase templates
- [x] 3.2 Implement instruction appending mechanism (phase rules + monitoring-result)
- [x] 3.3 Create templates for non-phase changes (issue, tracking, description, queue)
- [x] 3.4 Update template context to include change information
- [x] 3.5 Implement phase template discovery using glob pattern "*{phase}" (e.g., "*planning")

## 4. WorkflowMonitorTask Integration
- [x] 4.1 Modify _process_workflow_content to use comparison-first approach
- [x] 4.2 Integrate change detection before cache update
- [x] 4.3 Queue appropriate instructions based on detected changes
- [x] 4.4 Ensure proper error handling during comparison
- [x] 4.5 Update cache timing (compare → generate events → update cache)

## 5. Result Instruction Appending
- [x] 5.1 Modify workflow instruction queuing to support instruction appending
- [x] 5.2 Ensure phase transition instructions include both phase rules and monitoring result
- [x] 5.3 Handle multiple change types in single workflow update
- [x] 5.4 Maintain proper instruction ordering and formatting

## 6. Testing and Validation
- [x] 6.1 Test phase transition detection with rule inclusion
- [x] 6.2 Test issue/tracking/description change detection
- [x] 6.3 Test queue change detection (add/remove items)
- [x] 6.4 Test startup behavior (no previous cached state)
- [x] 6.5 Test multiple simultaneous changes
- [x] 6.6 Test instruction appending works correctly

## 7. Check Phase
- [x] 7.1 Run all existing workflow tests
- [x] 7.2 Verify semantic change detection works with real workflow files
- [x] 7.3 Confirm phase rules are properly included on transitions
- [x] 7.4 Validate template rendering and instruction appending
- [x] 7.5 Test edge cases (malformed workflow files, parsing errors)
- [ ] 7.6 **READY FOR REVIEW** - Request user review of implementation
