# Spec Delta

## ADDED Requirements

### Requirement: Rendered elicitation sections

The renderer SHALL provide an asynchronous `elicit` section extension for interactive command and skill templates. The extension SHALL select a named frontmatter form only when Mustache renders that section. It SHALL await unresolved required input and, once input is available, render the enclosed section with the accepted values in the normal template context.

#### Scenario: Selected section awaits input

- **WHEN** rendering reaches an `elicit` section for a declared form with missing required properties
- **THEN** Guide SHALL await that form's input before rendering the enclosed section

#### Scenario: Accepted input renders the section

- **WHEN** the client supplies valid values for an invoked form
- **THEN** Guide SHALL render the enclosed section with those values available through normal keyword context

#### Scenario: Conditional branch selects direct instructions

- **WHEN** a template's rendered condition excludes an `elicit` section
- **THEN** Guide SHALL complete the selected branch without scanning or requesting its form

## REMOVED Requirements

### Requirement: Elicitation-aware partial property collection

**Reason**: Collecting declarations before rendering can select forms from branches and partials that do not render.

**Migration**: Move form selection into `elicit` sections in the template or rendered partial that uses each form.

### Requirement: Interactive frontmatter preflight evaluation

**Reason**: Interactive input is selected by rendered sections rather than a pre-render frontmatter scan.

**Migration**: Keep form schemas in frontmatter and invoke them from the rendered template body.
