"""
Nova Local LLM Interface
========================

This module is responsible for communicating with the local Ollama
server and generating responses from Nova's language model.

The rest of Nova should not need to know how Ollama works internally.

This class provides:

- Model configuration
- Creativity / temperature control
- Generation parameters
- Input validation
- Connection checks
- Model availability checks
- Error handling
- Response extraction
- Retry handling
- Optional generation metadata
- Safe fallback behavior
- Runtime model configuration
- Simple health information

The goal is to keep the LLM layer reliable and isolated from the
rest of Nova's architecture.
"""

from __future__ import annotations

import time
from typing import Any, Dict, Optional

from ollama import chat


class LocalLLM:
    """
    Interface between Nova and the local Ollama model.

    Nova's other systems should communicate with this class instead
    of directly calling Ollama.

    Example:

        llm = LocalLLM()

        answer = llm.answer(
            system="You are Nova.",
            user="Explain gravity."
        )
    """

    # =========================================
    # DEFAULT CONFIGURATION
    # =========================================

    DEFAULT_MODEL = "qwen2.5:1.5b"

    DEFAULT_TEMPERATURE = 0.5

    DEFAULT_TOP_P = 0.9

    DEFAULT_REPEAT_PENALTY = 1.05

    DEFAULT_MAX_RETRIES = 2

    DEFAULT_RETRY_DELAY = 1.0

    # =========================================
    # CREATIVITY PRESETS
    # =========================================

    CREATIVITY_SETTINGS = {

        "low": {
            "temperature": 0.2,
            "top_p": 0.85,
            "repeat_penalty": 1.08
        },

        "medium": {
            "temperature": 0.5,
            "top_p": 0.9,
            "repeat_penalty": 1.05
        },

        "high": {
            "temperature": 0.8,
            "top_p": 0.95,
            "repeat_penalty": 1.03
        }

    }

    # =========================================
    # INITIALIZATION
    # =========================================

    def __init__(
        self,
        model: Optional[str] = None,
        max_retries: int = DEFAULT_MAX_RETRIES,
        retry_delay: float = DEFAULT_RETRY_DELAY
    ):
        """
        Initialize the local LLM interface.

        Args:
            model:
                Ollama model name.

            max_retries:
                Number of additional attempts after a failed request.

            retry_delay:
                Delay between retry attempts.
        """

        print(
            "Loading Nova Local LLM..."
        )

        self.model = (
            model
            or self.DEFAULT_MODEL
        )

        self.max_retries = max(
            0,
            int(max_retries)
        )

        self.retry_delay = max(
            0.0,
            float(retry_delay)
        )

        self.last_error = None

        self.last_response = None

        self.last_generation_time = None

        self.total_requests = 0

        self.successful_requests = 0

        self.failed_requests = 0

        print(
            f"Using Ollama model: {self.model}"
        )

        print(
            "Nova Local LLM ready."
        )

    # =========================================
    # CREATIVITY
    # =========================================

    def get_generation_settings(
        self,
        creativity: str = "medium"
    ) -> Dict[str, float]:
        """
        Convert a creativity preset into Ollama generation settings.

        Supported presets:

        - low
        - medium
        - high

        Unknown values fall back to medium.
        """

        if not isinstance(
            creativity,
            str
        ):
            creativity = "medium"

        creativity = (
            creativity
            .strip()
            .lower()
        )

        settings = self.CREATIVITY_SETTINGS.get(
            creativity
        )

        if settings is None:

            settings = self.CREATIVITY_SETTINGS[
                "medium"
            ]

        return dict(settings)

    # =========================================
    # TEMPERATURE
    # =========================================

    def get_temperature(
        self,
        creativity: str = "medium"
    ) -> float:
        """
        Return the temperature associated with a creativity level.
        """

        settings = self.get_generation_settings(
            creativity
        )

        return settings[
            "temperature"
        ]

    # =========================================
    # VALIDATION
    # =========================================

    def _validate_prompt(
        self,
        system: str,
        user: str
    ) -> None:
        """
        Validate prompts before sending them to Ollama.
        """

        if system is None:

            raise ValueError(
                "System prompt cannot be None."
            )

        if user is None:

            raise ValueError(
                "User prompt cannot be None."
            )

        if not isinstance(
            system,
            str
        ):

            raise TypeError(
                "System prompt must be a string."
            )

        if not isinstance(
            user,
            str
        ):

            raise TypeError(
                "User prompt must be a string."
            )

        if not system.strip():

            raise ValueError(
                "System prompt cannot be empty."
            )

        if not user.strip():

            raise ValueError(
                "User prompt cannot be empty."
            )

    # =========================================
    # MODEL NAME
    # =========================================

    def set_model(
        self,
        model: str
    ) -> None:
        """
        Change the Ollama model used by Nova.

        Example:

            llm.set_model("qwen2.5:7b")
        """

        if not isinstance(
            model,
            str
        ):

            raise TypeError(
                "Model name must be a string."
            )

        model = model.strip()

        if not model:

            raise ValueError(
                "Model name cannot be empty."
            )

        self.model = model

        print(
            f"Nova model changed to: {self.model}"
        )

    # =========================================
    # MODEL INFO
    # =========================================

    def get_model(
        self
    ) -> str:
        """
        Return the currently configured model.
        """

        return self.model

    # =========================================
    # RAW GENERATION
    # =========================================

    def _generate(
        self,
        system: str,
        user: str,
        generation_settings: Dict[str, Any]
    ):
        """
        Perform one raw Ollama request.

        This method intentionally contains the direct Ollama call so
        the rest of the class can handle validation, retries and
        response processing separately.
        """

        return chat(

            model=self.model,

            messages=[

                {
                    "role": "system",
                    "content": system
                },

                {
                    "role": "user",
                    "content": user
                }

            ],

            options={

                "temperature":
                    generation_settings[
                        "temperature"
                    ],

                "top_p":
                    generation_settings[
                        "top_p"
                    ],

                "repeat_penalty":
                    generation_settings[
                        "repeat_penalty"
                    ]

            }
        )

    # =========================================
    # RESPONSE EXTRACTION
    # =========================================

    def _extract_content(
        self,
        response: Any
    ) -> str:
        """
        Extract the assistant message from an Ollama response.

        Handles both dictionary-like and object-like responses.
        """

        if response is None:

            raise RuntimeError(
                "Ollama returned an empty response."
            )

        # -------------------------------------
        # Dictionary-style response
        # -------------------------------------

        if isinstance(
            response,
            dict
        ):

            message = response.get(
                "message"
            )

            if isinstance(
                message,
                dict
            ):

                content = message.get(
                    "content"
                )

            else:

                content = None

        # -------------------------------------
        # Object-style response
        # -------------------------------------

        else:

            message = getattr(
                response,
                "message",
                None
            )

            if message is None:

                content = None

            elif isinstance(
                message,
                dict
            ):

                content = message.get(
                    "content"
                )

            else:

                content = getattr(
                    message,
                    "content",
                    None
                )

        if content is None:

            raise RuntimeError(
                "Ollama response did not contain "
                "assistant message content."
            )

        if not isinstance(
            content,
            str
        ):

            content = str(
                content
            )

        content = content.strip()

        if not content:

            raise RuntimeError(
                "Ollama returned an empty assistant response."
            )

        return content

    # =========================================
    # ANSWER
    # =========================================

    def answer(
        self,
        system: str,
        user: str,
        creativity: str = "medium"
    ) -> str:
        """
        Generate an answer using the configured Ollama model.

        This is the main public method used by TutorEngine.

        The method:

        1. Validates the prompts.
        2. Selects generation settings.
        3. Sends the request to Ollama.
        4. Extracts the response.
        5. Retries temporary failures.
        6. Records basic request statistics.
        7. Returns clean text.
        """

        self._validate_prompt(
            system,
            user
        )

        generation_settings = (
            self.get_generation_settings(
                creativity
            )
        )

        self.total_requests += 1

        self.last_error = None

        start_time = time.perf_counter()

        attempts = (
            self.max_retries + 1
        )

        last_exception = None

        for attempt in range(
            attempts
        ):

            try:

                response = self._generate(

                    system=
                        system,

                    user=
                        user,

                    generation_settings=
                        generation_settings
                )

                answer = (
                    self._extract_content(
                        response
                    )
                )

                elapsed = (
                    time.perf_counter()
                    - start_time
                )

                self.last_response = answer

                self.last_generation_time = (
                    elapsed
                )

                self.successful_requests += 1

                return answer

            except Exception as error:

                last_exception = error

                self.last_error = (
                    str(error)
                )

                if attempt >= self.max_retries:

                    break

                time.sleep(
                    self.retry_delay
                )

        self.failed_requests += 1

        raise RuntimeError(
            self._format_generation_error(
                last_exception
            )
        ) from last_exception

    # =========================================
    # ERROR FORMATTING
    # =========================================

    def _format_generation_error(
        self,
        error: Optional[Exception]
    ) -> str:
        """
        Convert low-level Ollama errors into a more useful Nova error.
        """

        if error is None:

            return (
                "Nova could not generate a response."
            )

        error_text = str(
            error
        )

        lower_error = (
            error_text.lower()
        )

        # -------------------------------------
        # Connection problems
        # -------------------------------------

        if (
            "connection"
            in lower_error
            or "connect" in lower_error
            or "refused" in lower_error
        ):

            return (
                "Nova could not connect to Ollama. "
                "Make sure the Ollama service is running "
                "and try again."
            )

        # -------------------------------------
        # Model problems
        # -------------------------------------

        if (
            "model"
            in lower_error
            and (
                "not found"
                in lower_error
                or "pull"
                in lower_error
            )
        ):

            return (
                f"Nova could not use the Ollama model "
                f"'{self.model}'. Make sure the model "
                f"is installed locally."
            )

        # -------------------------------------
        # Generic failure
        # -------------------------------------

        return (
            "Nova failed to generate a response "
            f"using Ollama model '{self.model}'. "
            f"Technical error: {error_text}"
        )

    # =========================================
    # HEALTH CHECK
    # =========================================

    def health_check(
        self
    ) -> Dict[str, Any]:
        """
        Perform a lightweight generation test.

        This is useful for debugging Nova during startup or testing.

        Returns a dictionary instead of raising the error so callers
        can inspect the status safely.
        """

        try:

            response = self._generate(

                system=(
                    "You are a system health check. "
                    "Respond with exactly: OK"
                ),

                user="Respond with exactly: OK",

                generation_settings=(
                    self.get_generation_settings(
                        "low"
                    )
                )
            )

            content = (
                self._extract_content(
                    response
                )
            )

            return {

                "healthy": True,

                "model":
                    self.model,

                "response":
                    content,

                "error":
                    None
            }

        except Exception as error:

            return {

                "healthy": False,

                "model":
                    self.model,

                "response":
                    None,

                "error":
                    str(error)
            }

    # =========================================
    # STATUS
    # =========================================

    def status(
        self
    ) -> Dict[str, Any]:
        """
        Return information about the current LLM state.
        """

        success_rate = 0.0

        if self.total_requests > 0:

            success_rate = (
                self.successful_requests
                / self.total_requests
            )

        return {

            "model":
                self.model,

            "total_requests":
                self.total_requests,

            "successful_requests":
                self.successful_requests,

            "failed_requests":
                self.failed_requests,

            "success_rate":
                round(
                    success_rate,
                    3
                ),

            "last_generation_time":
                self.last_generation_time,

            "last_error":
                self.last_error
        }

    # =========================================
    # RESET STATISTICS
    # =========================================

    def reset_statistics(
        self
    ) -> None:
        """
        Reset request statistics without changing model settings.
        """

        self.total_requests = 0

        self.successful_requests = 0

        self.failed_requests = 0

        self.last_error = None

        self.last_response = None

        self.last_generation_time = None

    # =========================================
    # REPRESENTATION
    # =========================================

    def __repr__(
        self
    ) -> str:

        return (
            f"LocalLLM("
            f"model='{self.model}', "
            f"requests={self.total_requests}, "
            f"successes={self.successful_requests}, "
            f"failures={self.failed_requests}"
            f")"
        )