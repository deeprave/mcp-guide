# Stored Documents

Stored documents let you add content to mcp-guide that doesn't live as files in your project's docroot. You can ingest local files, fetch content from URLs, or have the agent store content directly — and it all becomes discoverable alongside your regular category content.

## What Are Stored Documents?

Normally, mcp-guide discovers content by scanning category directories for files matching configured patterns. Stored documents extend this by adding content to a category's document store. Once stored, these documents appear alongside filesystem documents when you query a category.

This is useful for:

- Adding external reference material (API docs, style guides, specifications)
- Storing content fetched from URLs
- Persisting agent-generated content across sessions

## Adding Documents

### From a Local File

Use the `:document/add` command to ingest a file from your filesystem:

```
guide://_document/add/docs/%2Fpath%2Fto%2Ffile.md
guide://_document/add/docs/%2Fpath%2Fto%2Ffile.md?as=custom-name
guide://_document/add/docs/%2Fpath%2Fto%2Ffile.md?force          # Overwrite if exists
```

The document name defaults to the filename (without extension). Use `--as` to give it a different name.

### From a URL

Fetch and store content directly from a URL:

```
guide://_document/add-url/docs/https%3A%2F%2Fexample.com%2Fapi-reference
guide://_document/add-url/docs/https%3A%2F%2Fexample.com%2Fguide?as=api-guide
```

The agent fetches the content and stores it in the specified category.

### Document Types

By default, stored documents inherit the standard type. You can specify a type when adding:

```
guide://_document/add/docs/%2Fpath%2Fto%2Ffile.md?agent-instruction
guide://_document/add/docs/%2Fpath%2Fto%2Ffile.md?agent-info
guide://_document/add/docs/%2Fpath%2Fto%2Ffile.md?user-info
```

## Viewing Stored Documents

List what's stored in a category:

```
guide://_document/list/docs
```

View a specific stored document:

```
guide://_document/show/docs/my-document
```

## Source Filtering

When listing files in a category, you can filter by source to see just filesystem documents, just stored documents, or both. This is available through the `category_list_files` tool's `source` parameter:

- `source: "files"` — filesystem documents only
- `source: "stored"` — stored documents only
- Omit `source` — both (default)

This is useful when you want to see what's been added to the store versus what exists on disk.

## Managing Documents

### Updating

Update a stored document's name, category, or metadata:

```
guide://_document/update/docs/my-document?new-name=new-name
guide://_document/update/docs/my-document?new-category=other-category
```

### Removing

Remove a stored document from a category:

```
guide://_document/remove/docs/my-document
```

This only removes the stored copy — it doesn't affect any original files on disk.

## How It Fits Together

Stored documents integrate seamlessly with the rest of mcp-guide:

- They appear in category queries (`guide://docs`)
- They respect the same frontmatter and type system as file-based documents
- They're included when collections reference the category
- They persist across sessions in the document store

Think of stored documents as a way to extend your project's content without cluttering your filesystem.

## Next Steps

- **[Content Management](content-management.md)** — Categories, collections, and expressions
- **[Documents](documents.md)** — Document structure, frontmatter, and templates
- **[Guide URIs](guide-uris.md)** — Accessing content via the `guide://` URI scheme
- **[Commands](commands.md)** — Full command reference
