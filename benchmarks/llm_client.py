"""LLM client for code generation.

Provides abstract interface and implementations for different LLM providers.
"""

import os
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


def load_dotenv() -> None:
    """Load environment variables from .env file if it exists."""
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()
                # Only set if not already set with a non-empty value
                if not os.environ.get(key):
                    os.environ[key] = value


# Load .env on module import
load_dotenv()


@dataclass
class GenerationResult:
    """Result of LLM code generation.

    Attributes:
        code: The generated code.
        model: Which model generated it.
        tokens_used: Total tokens consumed.
        latency_ms: API call latency.
    """

    code: str
    model: str
    tokens_used: int
    latency_ms: float


class LLMClient(ABC):
    """Abstract base class for LLM clients."""

    @abstractmethod
    def generate(
        self,
        prompt: str,
        max_tokens: int = 2048,
        temperature: float = 0.0,
    ) -> GenerationResult:
        """Generate code from a prompt.

        Args:
            prompt: The prompt to send to the LLM.
            max_tokens: Maximum tokens to generate.
            temperature: Sampling temperature.

        Returns:
            GenerationResult with generated code and metadata.
        """
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return the model name."""
        pass


class MockClient(LLMClient):
    """Mock LLM client for testing without API calls.

    Returns pre-defined responses based on the task description.
    """

    def __init__(self) -> None:
        """Initialize the mock client."""
        self._responses: dict[str, dict[str, str]] = {
            "filter_001": {
                "anka": """PIPELINE filter_large_orders:
    INPUT orders: TABLE[order_id: INT, customer: STRING, amount: DECIMAL]

    STEP filter_large:
        FILTER orders
        WHERE amount > 1000
        INTO result

    OUTPUT result
""",
                "python": """def transform(data):
    return [row for row in data['orders'] if row['amount'] > 1000]
""",
            },
            "default": {
                "anka": """PIPELINE task:
    INPUT data: TABLE[x: INT]
    OUTPUT data
""",
                "python": """def transform(data):
    return list(data.values())[0]
""",
            },
        }

    def generate(
        self,
        prompt: str,
        max_tokens: int = 2048,
        temperature: float = 0.0,
    ) -> GenerationResult:
        """Generate code from a prompt using mock responses.

        Determines task ID from prompt content and returns corresponding mock.
        """
        start_time = time.perf_counter()

        # Determine language from prompt
        language = "anka" if "Anka" in prompt else "python"

        # Determine task ID from prompt (look for task patterns)
        task_id = "default"
        if "amount is greater than 1000" in prompt.lower():
            task_id = "filter_001"

        responses = self._responses.get(task_id, self._responses["default"])
        code = responses.get(language, responses["anka"])

        latency_ms = (time.perf_counter() - start_time) * 1000

        return GenerationResult(
            code=code,
            model="mock",
            tokens_used=len(prompt.split()) + len(code.split()),
            latency_ms=latency_ms,
        )

    @property
    def model_name(self) -> str:
        """Return the model name."""
        return "mock"


class AnthropicClient(LLMClient):
    """LLM client using Anthropic's Claude API.

    Requires ANTHROPIC_API_KEY environment variable.
    """

    def __init__(
        self,
        model: str = "claude-3-5-sonnet-20241022",
        api_key: Optional[str] = None,
    ) -> None:
        """Initialize the Anthropic client.

        Args:
            model: Model ID to use.
            api_key: API key (defaults to ANTHROPIC_API_KEY env var).

        Raises:
            ImportError: If anthropic package is not installed.
            ValueError: If no API key is provided.
        """
        try:
            import anthropic
        except ImportError as e:
            raise ImportError(
                "anthropic package required. Install with: pip install anthropic"
            ) from e

        self._api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self._api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY environment variable not set. "
                "Set it or pass api_key to the constructor."
            )

        self._model = model
        self._client = anthropic.Anthropic(api_key=self._api_key)

    def generate(
        self,
        prompt: str,
        max_tokens: int = 2048,
        temperature: float = 0.0,
    ) -> GenerationResult:
        """Generate code from a prompt using Claude.

        Args:
            prompt: The prompt to send.
            max_tokens: Maximum tokens to generate.
            temperature: Sampling temperature.

        Returns:
            GenerationResult with generated code and metadata.
        """
        start_time = time.perf_counter()

        response = self._client.messages.create(
            model=self._model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}],
        )

        latency_ms = (time.perf_counter() - start_time) * 1000

        # Extract text from response
        code = ""
        for block in response.content:
            if hasattr(block, "text"):
                code += block.text

        # Extract code from markdown code blocks if present
        code = extract_code_from_markdown(code)

        tokens_used = response.usage.input_tokens + response.usage.output_tokens

        return GenerationResult(
            code=code,
            model=self._model,
            tokens_used=tokens_used,
            latency_ms=latency_ms,
        )

    @property
    def model_name(self) -> str:
        """Return the model name."""
        return self._model


def extract_code_from_markdown(text: str) -> str:
    """Extract code from markdown code blocks.

    Args:
        text: Text that may contain markdown code blocks.

    Returns:
        The code content, or original text if no code blocks found.
    """
    lines = text.strip().split("\n")

    # Look for code blocks
    in_code_block = False
    code_lines: list[str] = []

    for line in lines:
        if line.startswith("```"):
            if in_code_block:
                # End of code block
                break
            else:
                # Start of code block
                in_code_block = True
                continue

        if in_code_block:
            code_lines.append(line)

    if code_lines:
        return "\n".join(code_lines)

    # No code block found, return original text
    return text.strip()


class GoogleClient(LLMClient):
    """LLM client using Google's Gemini API.

    Requires GOOGLE_API_KEY environment variable.
    """

    def __init__(
        self,
        model: str = "gemini-1.5-flash",
        api_key: Optional[str] = None,
    ) -> None:
        """Initialize the Google client.

        Args:
            model: Model ID to use.
            api_key: API key (defaults to GOOGLE_API_KEY env var).

        Raises:
            ImportError: If google-generativeai package is not installed.
            ValueError: If no API key is provided.
        """
        try:
            import google.generativeai as genai
        except ImportError as e:
            raise ImportError(
                "google-generativeai package required. Install with: pip install google-generativeai"
            ) from e

        self._api_key = api_key or os.environ.get("GOOGLE_API_KEY")
        if not self._api_key:
            raise ValueError(
                "GOOGLE_API_KEY environment variable not set. "
                "Set it or pass api_key to the constructor."
            )

        self._model = model
        genai.configure(api_key=self._api_key)
        self._genai = genai

    def generate(
        self,
        prompt: str,
        max_tokens: int = 2048,
        temperature: float = 0.0,
    ) -> GenerationResult:
        """Generate code from a prompt using Gemini.

        Args:
            prompt: The prompt to send.
            max_tokens: Maximum tokens to generate.
            temperature: Sampling temperature.

        Returns:
            GenerationResult with generated code and metadata.
        """
        start_time = time.perf_counter()

        model_obj = self._genai.GenerativeModel(self._model)

        response = model_obj.generate_content(
            prompt,
            generation_config={
                'temperature': temperature,
                'max_output_tokens': max_tokens,
            }
        )

        latency_ms = (time.perf_counter() - start_time) * 1000

        # Extract text from response
        code = response.text if response.text else ""

        # Extract code from markdown code blocks if present
        code = extract_code_from_markdown(code)

        # Gemini doesn't always provide token counts, estimate
        tokens_used = len(prompt.split()) + len(code.split())

        return GenerationResult(
            code=code,
            model=self._model,
            tokens_used=tokens_used,
            latency_ms=latency_ms,
        )

    @property
    def model_name(self) -> str:
        """Return the model name."""
        return self._model


class OpenAIClient(LLMClient):
    """LLM client using OpenAI's API.

    Requires OPENAI_API_KEY environment variable.
    """

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        api_key: Optional[str] = None,
    ) -> None:
        """Initialize the OpenAI client.

        Args:
            model: Model ID to use.
            api_key: API key (defaults to OPENAI_API_KEY env var).

        Raises:
            ImportError: If openai package is not installed.
            ValueError: If no API key is provided.
        """
        try:
            import openai
        except ImportError as e:
            raise ImportError(
                "openai package required. Install with: pip install openai"
            ) from e

        self._api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self._api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable not set. "
                "Set it or pass api_key to the constructor."
            )

        self._model = model
        self._client = openai.OpenAI(api_key=self._api_key)

    def generate(
        self,
        prompt: str,
        max_tokens: int = 2048,
        temperature: float = 0.0,
    ) -> GenerationResult:
        """Generate code from a prompt using OpenAI.

        Args:
            prompt: The prompt to send.
            max_tokens: Maximum tokens to generate.
            temperature: Sampling temperature.

        Returns:
            GenerationResult with generated code and metadata.
        """
        start_time = time.perf_counter()

        response = self._client.chat.completions.create(
            model=self._model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}],
        )

        latency_ms = (time.perf_counter() - start_time) * 1000

        # Extract text from response
        code = response.choices[0].message.content or ""

        # Extract code from markdown code blocks if present
        code = extract_code_from_markdown(code)

        tokens_used = (response.usage.prompt_tokens + response.usage.completion_tokens
                       if response.usage else 0)

        return GenerationResult(
            code=code,
            model=self._model,
            tokens_used=tokens_used,
            latency_ms=latency_ms,
        )

    @property
    def model_name(self) -> str:
        """Return the model name."""
        return self._model


def get_llm_client(
    provider: str = "mock",
    model: Optional[str] = None,
    api_key: Optional[str] = None,
) -> LLMClient:
    """Get an LLM client instance.

    Args:
        provider: "mock", "anthropic", "openai", or "google".
        model: Model ID (provider-specific).
        api_key: API key for the provider.

    Returns:
        LLMClient instance.

    Raises:
        ValueError: If provider is not supported.
    """
    if provider == "mock":
        return MockClient()
    elif provider == "anthropic":
        kwargs: dict = {}
        if model:
            kwargs["model"] = model
        if api_key:
            kwargs["api_key"] = api_key
        return AnthropicClient(**kwargs)
    elif provider == "openai":
        kwargs = {}
        if model:
            kwargs["model"] = model
        if api_key:
            kwargs["api_key"] = api_key
        return OpenAIClient(**kwargs)
    elif provider == "google":
        kwargs = {}
        if model:
            kwargs["model"] = model
        if api_key:
            kwargs["api_key"] = api_key
        return GoogleClient(**kwargs)
    else:
        raise ValueError(f"Unsupported provider: {provider}")
