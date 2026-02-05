## ADDED Requirements

### Requirement: Instruction Acknowledgement Tracking
The TaskManager SHALL provide acknowledgement-based instruction tracking with automatic retry.

#### Scenario: Queue instruction with acknowledgement
- **WHEN** a task calls queue_instruction_with_ack(content, max_retries)
- **THEN** return a unique instruction ID for tracking
- **AND** add instruction to pending queue
- **AND** store instruction metadata for retry tracking

#### Scenario: Acknowledge instruction receipt
- **WHEN** a task calls acknowledge_instruction(instruction_id)
- **THEN** remove instruction from tracking
- **AND** prevent further retries of that instruction

#### Scenario: Deduplicate identical instructions
- **WHEN** queue_instruction_with_ack() is called with content already tracked
- **THEN** return existing instruction ID
- **AND** do not add duplicate to queue

### Requirement: Automatic Instruction Retry
The TaskManager SHALL automatically retry unacknowledged instructions during idle periods.

#### Scenario: Retry during idle state
- **WHEN** RetryTask timer fires and instruction queue is empty
- **THEN** requeue all unacknowledged instructions that have been waiting at least 30 seconds
- **AND** increment retry counter for each instruction

#### Scenario: Skip retry when queue active
- **WHEN** RetryTask timer fires and instruction queue is not empty
- **THEN** do not retry any instructions
- **AND** wait for next timer interval

#### Scenario: Skip retry when instruction too recent
- **WHEN** RetryTask checks unacknowledged instruction
- **AND** instruction was sent less than 30 seconds ago
- **THEN** do not retry that instruction
- **AND** wait for next timer interval

#### Scenario: Escalate instruction urgency
- **WHEN** retrying an instruction for the 2nd time
- **THEN** prefix content with "**IMPORTANT:** "
- **WHEN** retrying an instruction for the 3rd+ time
- **THEN** prefix content with "**URGENT:** "

#### Scenario: Give up after max retries
- **WHEN** an instruction reaches max_retries without acknowledgement
- **THEN** remove from tracking
- **AND** log warning with instruction content
- **AND** do not retry again

### Requirement: RetryTask Timer Monitoring
The TaskManager SHALL provide a RetryTask that monitors for unacknowledged instructions.

#### Scenario: RetryTask initialization
- **WHEN** TaskManager initializes
- **THEN** create RetryTask with 60-second timer interval
- **AND** subscribe to timer events

#### Scenario: RetryTask idle detection
- **WHEN** RetryTask receives timer event
- **THEN** check if instruction queue is empty
- **AND** trigger retry_unacknowledged() if idle
