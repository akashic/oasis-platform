"""Integration tests for engagement-to-adaptive turn handoff."""

from __future__ import annotations

import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from pipecat.frames.frames import (
    BotStoppedSpeakingFrame,
    LLMMessagesAppendFrame,
    TranscriptionFrame,
    UserStartedSpeakingFrame,
    UserStoppedSpeakingFrame,
)
from pipecat.pipeline.pipeline import Pipeline
from pipecat.tests.utils import SleepFrame, run_test

from app.engagement.adaptive import AdaptivePolicy, AdaptiveSignals
from app.models.engagement import AdaptiveAction
from app.pipeline.adaptive_processor import AdaptiveBehaviorProcessor
from app.pipeline.engagement_processor import EngagementProcessor


_PACE = SleepFrame(sleep=0.05)


def _mock_db_factory():
    session = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    factory = MagicMock()
    factory.return_value.__aenter__ = AsyncMock(return_value=session)
    factory.return_value.__aexit__ = AsyncMock(return_value=False)
    return factory, session


def _tf(text: str) -> TranscriptionFrame:
    return TranscriptionFrame(text=text, user_id="u", timestamp="t")


def _paced(*frames):
    paced = []
    for frame in frames:
        paced.extend([frame, _PACE])
    return paced


def _make_pipeline(mode: str = "live"):
    db_factory, db = _mock_db_factory()
    state = MagicMock()
    state.sequence = 7
    signals = AdaptiveSignals()
    policy = AdaptivePolicy.from_dict(
        {
            "mode": mode,
            "rules": [
                {
                    "on": "very_short_answer",
                    "action": "encourage_elaboration",
                }
            ],
        }
    )
    engagement = EngagementProcessor(
        session_id=uuid.uuid4(),
        db_session_factory=db_factory,
        transcript_state=state,
        language="en",
        signals=signals,
    )
    adaptive = AdaptiveBehaviorProcessor(
        session_id=uuid.uuid4(),
        db_session_factory=db_factory,
        signals=signals,
        policy=policy,
    )
    return Pipeline([engagement, adaptive]), engagement, adaptive, signals, db


async def _drain(*processors) -> None:
    await asyncio.sleep(0)
    tasks = [
        task
        for processor in processors
        for task in list(processor._bg_tasks)
    ]
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)


def _adaptive_rows(db) -> list[AdaptiveAction]:
    return [
        call.args[0]
        for call in db.add.call_args_list
        if isinstance(call.args[0], AdaptiveAction)
    ]


@pytest.mark.asyncio
async def test_live_adapts_on_stop_after_final_transcription():
    """The normal analyzer ordering finalizes the turn on the stop frame."""
    pipeline, engagement, adaptive, signals, db = _make_pipeline()

    down, _ = await run_test(
        processor=pipeline,
        frames_to_send=_paced(
            BotStoppedSpeakingFrame(),
            UserStartedSpeakingFrame(),
            _tf("Yes."),
            UserStoppedSpeakingFrame(),
        ),
    )
    await _drain(engagement, adaptive)

    injected = [f for f in down if isinstance(f, LLMMessagesAppendFrame)]
    stop_index = next(
        i for i, frame in enumerate(down) if isinstance(frame, UserStoppedSpeakingFrame)
    )
    injection_index = next(
        i for i, frame in enumerate(down) if isinstance(frame, LLMMessagesAppendFrame)
    )

    assert signals.turn_id == 1
    assert len(injected) == 1
    assert injection_index < stop_index
    assert "invite them to say more" in injected[0].messages[0]["content"].lower()
    rows = _adaptive_rows(db)
    assert len(rows) == 1
    assert rows[0].transcript_sequence == 7
    assert rows[0].detail["applied"] is True


@pytest.mark.asyncio
async def test_live_adapts_when_stop_precedes_transcription():
    """A stop-before-STT ordering finalizes on the completing transcript."""
    pipeline, engagement, adaptive, signals, db = _make_pipeline()
    completing_transcript = _tf("Yes.")

    down, _ = await run_test(
        processor=pipeline,
        frames_to_send=_paced(
            BotStoppedSpeakingFrame(),
            UserStartedSpeakingFrame(),
            UserStoppedSpeakingFrame(),
            completing_transcript,
        ),
    )
    await _drain(engagement, adaptive)

    injection_index = next(
        i for i, frame in enumerate(down) if isinstance(frame, LLMMessagesAppendFrame)
    )
    transcript_index = next(
        i
        for i, frame in enumerate(down)
        if isinstance(frame, TranscriptionFrame) and frame.text == "Yes."
    )

    assert signals.turn_id == 1
    assert injection_index < transcript_index
    assert len(_adaptive_rows(db)) == 1


@pytest.mark.asyncio
async def test_intermediate_transcription_fragments_do_not_adapt():
    pipeline, engagement, adaptive, signals, db = _make_pipeline()

    down, _ = await run_test(
        processor=pipeline,
        frames_to_send=_paced(
            UserStartedSpeakingFrame(),
            _tf("Yes"),
            _tf("okay"),
            UserStoppedSpeakingFrame(),
        ),
    )
    await _drain(engagement, adaptive)

    transcription_indices = [
        i for i, frame in enumerate(down) if isinstance(frame, TranscriptionFrame)
    ]
    injection_indices = [
        i for i, frame in enumerate(down) if isinstance(frame, LLMMessagesAppendFrame)
    ]
    stop_index = next(
        i for i, frame in enumerate(down) if isinstance(frame, UserStoppedSpeakingFrame)
    )

    assert signals.turn_id == 1
    assert len(injection_indices) == 1
    assert max(transcription_indices) < injection_indices[0] < stop_index
    assert len(_adaptive_rows(db)) == 1


@pytest.mark.asyncio
async def test_shadow_records_without_injecting():
    pipeline, engagement, adaptive, signals, db = _make_pipeline(mode="shadow")

    down, _ = await run_test(
        processor=pipeline,
        frames_to_send=_paced(
            UserStartedSpeakingFrame(),
            _tf("Yes."),
            UserStoppedSpeakingFrame(),
        ),
    )
    await _drain(engagement, adaptive)

    assert signals.turn_id == 1
    assert not any(isinstance(f, LLMMessagesAppendFrame) for f in down)
    rows = _adaptive_rows(db)
    assert len(rows) == 1
    assert rows[0].mode == "shadow"
    assert rows[0].detail["applied"] is False


@pytest.mark.asyncio
async def test_two_complete_turns_adapt_exactly_once_each():
    pipeline, engagement, adaptive, signals, db = _make_pipeline()

    down, _ = await run_test(
        processor=pipeline,
        frames_to_send=_paced(
            UserStartedSpeakingFrame(),
            _tf("Yes."),
            UserStoppedSpeakingFrame(),
            BotStoppedSpeakingFrame(),
            UserStartedSpeakingFrame(),
            _tf("No."),
            UserStoppedSpeakingFrame(),
        ),
    )
    await _drain(engagement, adaptive)

    injected = [f for f in down if isinstance(f, LLMMessagesAppendFrame)]
    assert signals.turn_id == 2
    assert len(injected) == 2
    assert len(_adaptive_rows(db)) == 2
