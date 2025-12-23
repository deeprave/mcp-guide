Currently it is not possible to have multiple projects with the same project name.
They will get confused.
For example, if I had:
  ~/Projects/my-project
and
  ~/Projects/some-other-project/my-project

mcp-guide will treat them *both* as `my-project`.

This suggests an alternative way is needed to verify the client path.
The full path can be provided either by:
 - list/roots (for IDE agents)
 - PWD/CWD (for cli agents)
Using the full path, we can calculate and store an unambiguous hash - like a sha256 that verifies that
the name being used is the correct one.

The problem then:
- We don't want to use the hash as the project key, and this makes the configuration non-portable.
- how to disambiguate the same-named projects in the config file. Since they are used as keys.
  Do we change the key slightly, perhaps adding some portion of the hash to it?
  Do we convert the projects dictionary to a list?
- We may need to ask the user if they have moved the project or are adopting the project from elsewhere if the hash does not agree.
  Assuming that we make projects a list, then our project search becomes
    look for project using the basename
    if there is only 1, check the hash.
      if it agrees, then this is our project, return it
    if there are multiple using the same name then
      match the hash
        - match found, return that project
    if there are no matches or the user rejects any possible match then create a new project: same name, different hash
  This may make updating a little less performant.

