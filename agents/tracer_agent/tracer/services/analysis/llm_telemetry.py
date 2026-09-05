import logging

logger = logging.getLogger(__name__)

_CHARS_PER_TOKEN = 4


def log_llm_call(stage: str, batch_size: int, system: str, content: str, response: object) -> None:
    usage = getattr(response, "usage", None)
    sent_in = getattr(usage, "input_tokens", None)
    sent_out = getattr(usage, "output_tokens", None)
    stop = getattr(response, "stop_reason", "")
    logger.info(
        "[llm] %s batch=%d prompt_chars=%d (system=%d evidence=%d ~%d tok) "
        "in_tokens=%s out_tokens=%s stop=%s",
        stage,
        batch_size,
        len(system) + len(content),
        len(system),
        len(content),
        (len(system) + len(content)) // _CHARS_PER_TOKEN,
        sent_in,
        sent_out,
        stop,
    )
    if stop == "max_tokens":
        logger.warning(
            "[llm] %s batch=%d hit max_tokens — the reply was truncated and this batch "
            "will fall back to deterministic labels",
            stage,
            batch_size,
        )
