"""
Tests for System Prompts

Tests the system prompts and prompt generation in src/agent/prompts.py.
"""

from src.agent.prompts import (
    EXPLANATION_MODE_SUFFIX,
    SYSTEM_PROMPT,
    SYSTEM_PROMPT_MINIMAL,
    SYSTEM_PROMPT_READONLY,
    get_system_prompt,
)

# get_system_prompt() renders the ``{mcp_servers_info}`` placeholder. When no servers
# are provided it injects this default message, so expected prompts must be rendered the
# same way before comparing against the function output.
_DEFAULT_MCP_INFO = (
    "Currently, you do not have any MCP servers loaded. "
    "You can only respond using your base knowledge."
)


def _rendered(prompt: str) -> str:
    """Render a raw prompt constant the way ``get_system_prompt()`` does by default."""
    return prompt.replace("{mcp_servers_info}", _DEFAULT_MCP_INFO)


class TestSystemPromptConstants:
    """Tests for system prompt constant strings."""

    def test_system_prompt_not_empty(self):
        """Test main system prompt is defined."""
        assert SYSTEM_PROMPT
        assert len(SYSTEM_PROMPT) > 100

    def test_system_prompt_readonly_not_empty(self):
        """Test readonly system prompt is defined."""
        assert SYSTEM_PROMPT_READONLY
        assert len(SYSTEM_PROMPT_READONLY) > 100

    def test_system_prompt_minimal_not_empty(self):
        """Test minimal system prompt is defined."""
        assert SYSTEM_PROMPT_MINIMAL
        assert len(SYSTEM_PROMPT_MINIMAL) > 10

    def test_explanation_mode_suffix_not_empty(self):
        """Test explanation mode suffix is defined."""
        assert EXPLANATION_MODE_SUFFIX
        assert len(EXPLANATION_MODE_SUFFIX) > 100

    def test_system_prompt_contains_tools(self):
        """Test main prompt mentions available tools."""
        tools = ["list_tables", "describe_table", "read_data"]
        for tool in tools:
            assert tool in SYSTEM_PROMPT

    def test_system_prompt_references_mcp_tools(self):
        """Main prompt references MCP-provided tools.

        Write tools (insert_data, update_data, ...) are discovered dynamically through
        the connected MCP servers rather than enumerated in the prompt, so the prompt
        only needs to reference the MCP tool model.
        """
        assert "MCP servers" in SYSTEM_PROMPT
        assert "tools" in SYSTEM_PROMPT.lower()

    def test_readonly_prompt_no_write_tools(self):
        """Test readonly prompt doesn't list write operations as available."""
        for write_tool in ["insert_data", "update_data", "create_table", "drop_table"]:
            assert write_tool not in SYSTEM_PROMPT_READONLY

    def test_readonly_prompt_mentions_readonly(self):
        """Test readonly prompt mentions read-only mode."""
        assert (
            "READ-ONLY" in SYSTEM_PROMPT_READONLY or "read-only" in SYSTEM_PROMPT_READONLY.lower()
        )

    def test_explanation_mode_contains_educational_content(self):
        """Test explanation mode suffix contains educational guidance."""
        assert "explain" in EXPLANATION_MODE_SUFFIX.lower()
        assert "query" in EXPLANATION_MODE_SUFFIX.lower()
        assert "learning" in EXPLANATION_MODE_SUFFIX.lower() or "Learn" in EXPLANATION_MODE_SUFFIX


class TestGetSystemPrompt:
    """Tests for get_system_prompt function."""

    def test_default_prompt(self):
        """Test default parameters return full prompt."""
        prompt = get_system_prompt()
        assert prompt == _rendered(SYSTEM_PROMPT)

    def test_readonly_prompt(self):
        """Test readonly flag returns readonly prompt."""
        prompt = get_system_prompt(readonly=True)
        assert prompt == _rendered(SYSTEM_PROMPT_READONLY)

    def test_minimal_prompt(self):
        """Test minimal flag returns minimal prompt."""
        prompt = get_system_prompt(minimal=True)
        assert prompt == _rendered(SYSTEM_PROMPT_MINIMAL)

    def test_minimal_takes_precedence(self):
        """Test minimal flag takes precedence over readonly."""
        prompt = get_system_prompt(minimal=True, readonly=True)
        assert prompt == _rendered(SYSTEM_PROMPT_MINIMAL)

    def test_explain_mode_adds_suffix(self):
        """Test explain_mode adds explanation suffix."""
        prompt = get_system_prompt(explain_mode=True)
        assert EXPLANATION_MODE_SUFFIX in prompt
        assert prompt == _rendered(SYSTEM_PROMPT) + EXPLANATION_MODE_SUFFIX

    def test_readonly_with_explain_mode(self):
        """Test readonly with explain mode."""
        prompt = get_system_prompt(readonly=True, explain_mode=True)
        assert _rendered(SYSTEM_PROMPT_READONLY) in prompt
        assert EXPLANATION_MODE_SUFFIX in prompt

    def test_minimal_with_explain_mode(self):
        """Test minimal with explain mode."""
        prompt = get_system_prompt(minimal=True, explain_mode=True)
        assert _rendered(SYSTEM_PROMPT_MINIMAL) in prompt
        assert EXPLANATION_MODE_SUFFIX in prompt

    def test_all_combinations(self):
        """Test all parameter combinations are valid."""
        combinations = [
            (False, False, False),
            (True, False, False),
            (False, True, False),
            (True, True, False),
            (False, False, True),
            (True, False, True),
            (False, True, True),
            (True, True, True),
        ]

        for readonly, minimal, explain in combinations:
            prompt = get_system_prompt(
                readonly=readonly,
                minimal=minimal,
                explain_mode=explain,
            )
            assert isinstance(prompt, str)
            assert len(prompt) > 0


class TestPromptContent:
    """Tests for prompt content quality."""

    def test_main_prompt_has_workflow_guidelines(self):
        """Test main prompt includes workflow guidelines."""
        assert "Workflow" in SYSTEM_PROMPT or "workflow" in SYSTEM_PROMPT

    def test_main_prompt_has_safety_guidelines(self):
        """Test main prompt includes safety guidelines."""
        assert "Safety" in SYSTEM_PROMPT or "safety" in SYSTEM_PROMPT

    def test_prompts_are_well_formatted(self):
        """Test prompts use markdown formatting."""
        # Check for markdown headers
        assert "##" in SYSTEM_PROMPT
        assert "##" in SYSTEM_PROMPT_READONLY

    def test_prompts_have_tool_descriptions(self):
        """Test prompts describe what tools do."""
        assert "list_tables" in SYSTEM_PROMPT  # read tool reference
        assert "schema" in SYSTEM_PROMPT.lower()  # describe_table purpose
        assert "query" in SYSTEM_PROMPT.lower() or "Query" in SYSTEM_PROMPT

    def test_readonly_explains_limitation(self):
        """Test readonly prompt explains what user cannot do."""
        assert (
            "cannot" in SYSTEM_PROMPT_READONLY.lower()
            or "can't" in SYSTEM_PROMPT_READONLY.lower()
            or "only query" in SYSTEM_PROMPT_READONLY.lower()
        )

    def test_explanation_mode_has_example(self):
        """Test explanation mode includes example format."""
        assert "Example" in EXPLANATION_MODE_SUFFIX or "example" in EXPLANATION_MODE_SUFFIX.lower()

    def test_prompts_encourage_helpfulness(self):
        """Test prompts position agent as helpful."""
        assert "helpful" in SYSTEM_PROMPT.lower()
        assert "helpful" in SYSTEM_PROMPT_READONLY.lower()

    def test_prompts_mention_sql_server(self):
        """Test prompts mention SQL Server / database context."""
        assert "SQL Server" in SYSTEM_PROMPT
        # The readonly prompt describes database work generically rather than naming
        # the SQL Server backend explicitly.
        assert "database" in SYSTEM_PROMPT_READONLY.lower()


class TestPromptLength:
    """Tests for prompt length considerations."""

    def test_minimal_is_shortest(self):
        """Test minimal prompt is the shortest."""
        assert len(SYSTEM_PROMPT_MINIMAL) < len(SYSTEM_PROMPT_READONLY)
        assert len(SYSTEM_PROMPT_MINIMAL) < len(SYSTEM_PROMPT)

    def test_readonly_comparable_to_main(self):
        """Test readonly and main prompts are comparable length."""
        # Readonly should be shorter since fewer tools
        assert len(SYSTEM_PROMPT_READONLY) < len(SYSTEM_PROMPT)

    def test_explain_mode_adds_significant_content(self):
        """Test explanation mode adds substantial content."""
        base = get_system_prompt()
        with_explain = get_system_prompt(explain_mode=True)

        added_length = len(with_explain) - len(base)
        assert added_length > 500  # Should add significant content
