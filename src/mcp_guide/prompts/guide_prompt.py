# See src/mcp_guide/prompts/README.md for prompt documentation standards

"""Guide prompt implementation for direct content access."""

from typing import Optional

try:
    from mcp.server.fastmcp import Context
except ImportError:
    Context = None  # type: ignore

from mcp_core.result import Result
from mcp_guide.server import prompts
from mcp_guide.tools.tool_constants import INSTRUCTION_DISPLAY_ONLY
from mcp_guide.tools.tool_content import ContentArgs, internal_get_content

# MCP compatibility limit for variable arguments
MAX_PROMPT_ARGS = 15


@prompts.prompt()
async def guide(
    arg1: Optional[str] = None,
    arg2: Optional[str] = None,
    arg3: Optional[str] = None,
    arg4: Optional[str] = None,
    arg5: Optional[str] = None,
    arg6: Optional[str] = None,
    arg7: Optional[str] = None,
    arg8: Optional[str] = None,
    arg9: Optional[str] = None,
    argA: Optional[str] = None,
    argB: Optional[str] = None,
    argC: Optional[str] = None,
    argD: Optional[str] = None,
    argE: Optional[str] = None,
    argF: Optional[str] = None,
    ctx: Optional["Context"] = None,  # type: ignore[type-arg]
) -> str:
    """Direct access to guide content.

    Retrieves content from categories and collections without
    agent interpretation. Supports flexible argument patterns
    for content discovery and access.

    ## Conceptual Schema

    ```python
    def guide(*args: str) -> str:
        \"\"\"
        Args:
            *args: Variable string arguments for content specification
                  - Category names (e.g., 'docs', 'examples')
                  - Collection names (e.g., 'getting-started')
                  - Pattern specifications (e.g., 'docs/*.md')

        Returns:
            JSON string with formatted content results
        \"\"\"
    ```

    ## Usage Instructions

    ```bash
    # Single category
    @guide docs

    # Multiple categories
    @guide docs examples

    # Pattern filtering
    @guide docs/*.md
    ```

    ## Concrete Examples

    ```bash
    # Example 1: Get documentation content
    @guide docs
    # Returns: All content from docs category

    # Example 2: Multiple categories
    @guide docs examples tutorials
    # Returns: Combined content from all specified categories

    # Example 3: Pattern-based filtering
    @guide review/*.md
    # Returns: Only markdown files from review category
    ```
    """
    # Build argv list (stop at first None)
    argv = ["guide"]
    for arg in [arg1, arg2, arg3, arg4, arg5, arg6, arg7, arg8, arg9, argA, argB, argC, argD, argE, argF]:
        if arg is None:
            break
        argv.append(arg)

    # Check if arguments provided
    if len(argv) == 1 or (len(argv) == 2 and argv[1] == ""):  # No arguments or empty string
        result: Result[str] = Result.failure("Requires 1 or more arguments", error_type="validation")
        result.instruction = INSTRUCTION_DISPLAY_ONLY
        return result.to_json_str()

    # Use first argument as category/pattern
    category = argv[1]
    content_args = ContentArgs(category_or_collection=category, pattern=None)
    content_result = await internal_get_content(content_args, ctx)

    # Set instruction and return as JSON
    content_result.instruction = INSTRUCTION_DISPLAY_ONLY
    return content_result.to_json_str()
