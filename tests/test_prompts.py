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

    def test_system_prompt_contains_write_tools(self):
        """Test main prompt mentions write tools."""
        write_tools = ["insert_data", "update_data", "create_table", "drop_table"]
        for tool in write_tools:
            assert tool in SYSTEM_PROMPT

    def test_readonly_prompt_no_write_tools(self):
        """Test readonly prompt doesn't mention write operations as available."""
        # The readonly prompt should not list write tools as available
        assert (
            "insert_data" not in SYSTEM_PROMPT_READONLY.split("Available Tools")[1].split("##")[0]
        )

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
        assert prompt == SYSTEM_PROMPT

    def test_readonly_prompt(self):
        """Test readonly flag returns readonly prompt."""
        prompt = get_system_prompt(readonly=True)
        assert prompt == SYSTEM_PROMPT_READONLY

    def test_minimal_prompt(self):
        """Test minimal flag returns minimal prompt."""
        prompt = get_system_prompt(minimal=True)
        assert prompt == SYSTEM_PROMPT_MINIMAL

    def test_minimal_takes_precedence(self):
        """Test minimal flag takes precedence over readonly."""
        prompt = get_system_prompt(minimal=True, readonly=True)
        assert prompt == SYSTEM_PROMPT_MINIMAL

    def test_explain_mode_adds_suffix(self):
        """Test explain_mode adds explanation suffix."""
        prompt = get_system_prompt(explain_mode=True)
        assert EXPLANATION_MODE_SUFFIX in prompt
        assert prompt == SYSTEM_PROMPT + EXPLANATION_MODE_SUFFIX

    def test_readonly_with_explain_mode(self):
        """Test readonly with explain mode."""
        prompt = get_system_prompt(readonly=True, explain_mode=True)
        assert SYSTEM_PROMPT_READONLY in prompt
        assert EXPLANATION_MODE_SUFFIX in prompt

    def test_minimal_with_explain_mode(self):
        """Test minimal with explain mode."""
        prompt = get_system_prompt(minimal=True, explain_mode=True)
        assert SYSTEM_PROMPT_MINIMAL in prompt
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
        assert "List" in SYSTEM_PROMPT  # list_tables description
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
        """Test prompts mention SQL Server context."""
        assert "SQL Server" in SYSTEM_PROMPT
        assert "SQL Server" in SYSTEM_PROMPT_READONLY


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
