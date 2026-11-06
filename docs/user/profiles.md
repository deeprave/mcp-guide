# Profiles

Profiles give you quick project setup with pre-configured categories and collections.

## What are Profiles?

Think of profiles as additive project guidance. Instead of manually selecting every
document, apply profiles for the languages, frameworks, platforms, build systems,
and test stacks that genuinely apply to the project.

## Discovering Profiles

Ask your AI agent what's available:

```
list all project profiles
What profiles are available?
```

The agent will show you available profiles and what they add to your project.

## Using Profiles

Just ask your AI agent to apply them:

```
Apply the python profile
Add the jira profile
```

## How Profiles Work

Profiles are **additive** - they add categories and collections without removing existing ones. You can apply multiple profiles to build up your project configuration:

```
Apply the python profile
Apply the jira profile
```

This gives you Python + Jira setup combined. Profiles can also describe different
parts of one technology stack:

```
Apply the swift profile
Apply the swiftui profile
Apply the ios profile
Apply the xctest profile
```

This composes base Swift language guidance, SwiftUI guidance, iOS build and test
guidance, and XCTest guidance. Applying the same profile multiple times has no effect.

Apply the `testing` profile to add the language-neutral testing guidance for any project.

## Profile guidance layout

- `lang/` holds base language, framework, and additive aspect guidance.
- `lang/build/` holds language and platform build guidance.
- `checks/` holds testing and verification guidance only.

The bundled catalogue includes established language profiles such as C, Swift,
Objective-C, Ruby, Dart, Scala, Elixir, Clojure, Lua, R, F#, Haskell, and Zig;
additive profiles including Node.js, Angular, Svelte, Nuxt, NestJS, Rails, Laravel,
Symfony, ASP.NET Core, Flutter, React Native, SwiftUI, UIKit, AppKit, Swift
Concurrency, Swift Package Manager, testing, XCTest, and Swift Testing; and platform profiles
for macOS, iOS, iPadOS, watchOS, tvOS, visionOS, Android, Windows, Linux, and browser
automation. Use `list_profiles` to see the authoritative installed set.

## Template syntax profiles

Template syntax profiles are explicit, additive, and non-exclusive. Apply every
profile whose syntax the project actually uses; Guide does not infer an engine
from filenames, dependencies, or project layout. The Django profile includes
`django-templates`, but it does not imply Jinja2 or another third-party engine.

| Ecosystem | Profiles and primary references |
|---|---|
| Generic and Python | [`mustache`](https://github.com/mustache/spec), [`handlebars`](https://handlebarsjs.com/guide/), [`jinja2`](https://jinja.palletsprojects.com/en/stable/templates/), [`django-templates`](https://docs.djangoproject.com/en/stable/ref/templates/language/), [`mako`](https://www.makotemplates.org/), [`chameleon`](https://chameleon.readthedocs.io/) |
| JVM and Kotlin | [`velocity`](https://velocity.apache.org/engine/devel/), [`thymeleaf`](https://www.thymeleaf.org/documentation.html), [`freemarker`](https://freemarker.apache.org/docs/), [`jte`](https://jte.gg/), [`kotlinx-html`](https://kotlinlang.org/docs/typesafe-html-dsl.html) |
| Go | [`go-templates`](https://pkg.go.dev/html/template), [`templ`](https://templ.guide/), [`jet`](https://github.com/CloudyKit/jet), [`pongo2`](https://github.com/flosch/pongo2/tree/master/docs), [`gomponents`](https://www.gomponents.com/) |
| Rust | [`askama`](https://docs.rs/askama/), [`tera`](https://keats.github.io/tera/), [`minijinja`](https://docs.rs/minijinja/), [`handlebars-rust`](https://docs.rs/handlebars/), [`maud`](https://maud.lambda.xyz/), [`ructe`](https://docs.rs/ructe/), [`yarte`](https://github.com/botika/yarte) |
| JavaScript and TypeScript | [`jsx-tsx`](https://www.typescriptlang.org/docs/handbook/jsx.html), [`nunjucks`](https://mozilla.github.io/nunjucks/), [`ejs`](https://ejs.co/docs/), [`pug`](https://pugjs.org/) |
| PHP | [`blade`](https://laravel.com/docs/blade), [`twig`](https://twig.symfony.com/doc/), [`latte`](https://latte.nette.org/en/), [`smarty`](https://www.smarty.net/docs/en/) |
| Ruby | [`erb`](https://ruby-doc.org/stdlib/libdoc/erb/rdoc/ERB.html), [`slim`](https://slim-template.github.io/), [`haml`](https://haml.info/), [`liquid`](https://shopify.github.io/liquid/) |
| Swift and .NET | [`leaf`](https://docs.vapor.codes/leaf/overview/), [`stencil`](https://stencil.fuller.li/en/latest/), [`razor`](https://learn.microsoft.com/aspnet/core/razor-pages/), [`scriban`](https://github.com/scriban/scriban) |
| Other | [`stringtemplate`](https://www.stringtemplate.org/), [`pebble`](https://pebbletemplates.io/), [`qute`](https://quarkus.io/guides/qute), [`inja`](https://github.com/pantor/inja) |

`kotlinx-html`, `gomponents`, `maud`, JSX/TSX, and Razor are code-first markup
DSLs rather than text-template languages. Their profiles remain useful because
their output, escaping, composition, and rendering concerns are comparable.

## Methodology and Policies

Methodology preferences (TDD, BDD, SOLID, YAGNI, DDD) are no longer configured through profiles. Instead, they are selected through the `policies` category. See [Policy Selection](policies.md) for details.
