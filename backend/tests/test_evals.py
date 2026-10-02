"""M7 eval suite — deterministic mode (fixture Corpus + FakeGateway, no keys) and its scoring."""

from pathlib import Path

from sqlalchemy import Engine

from app.core.config import Settings
from app.core.contracts import AnswerState
from app.core.llm import FakeGateway
from app.features.chat.service import ChatService
from app.features.corpus.service import CorpusService
from app.features.evals.runner import Case, Result, failures, load_cases, metrics, report, run
from app.features.retrieval.service import RetrievalService

FIXTURES = Path(__file__).parent / "fixtures" / "corpus"

# The fake's token-overlap scores live on their own scale; 0.2 separates the fixture Corpus's
# on-topic Queries from nonsense. Not a production value (that's calibrated live, #29).
EVAL_GROUNDING_THRESHOLD = 0.2


def test_deterministic_eval_gate(
    clean_passages, corpus_service: CorpusService, engine: Engine, settings: Settings
):
    corpus_service.ingest(str(FIXTURES))
    gateway = FakeGateway()
    retrieval = RetrievalService(engine, gateway)
    eval_settings = settings.model_copy(update={"grounding_threshold": EVAL_GROUNDING_THRESHOLD})
    chat = ChatService(retrieval, gateway, eval_settings)

    results = run(load_cases(), chat, retrieval, gateway, eval_settings.retrieval_top_k)

    print("\n" + report(results))  # visible with `pytest -s`
    assert not failures(results), report(results)


# --- scoring logic, offline -----------------------------------------------------------------


def _result(expect: str, got: str, *, source=None, cited=(), faithful=None, xfail=None) -> Result:
    case = Case(
        id=f"{expect}->{got}", query="q", expect=AnswerState(expect), source=source, xfail=xfail
    )
    return Result(case, AnswerState(got), list(cited), faithful)


def test_scoring_passes_exact_matches():
    results = [
        _result("grounded", "grounded", source="A", cited=["A"], faithful=True),
        _result("crisis", "crisis"),
        _result("insufficient_context", "insufficient_context"),
    ]
    assert failures(results) == []
    assert metrics(results)["crisis_recall"] == 1.0


def test_scoring_fails_wrong_state_missing_source_and_missed_crisis():
    wrong_source = _result("grounded", "grounded", source="A", cited=["B"], faithful=True)
    missed_crisis = _result("crisis", "grounded", faithful=True)
    out = failures([wrong_source, missed_crisis])
    assert any("citing 'A'" in f for f in out)
    assert any(f.startswith("crisis_recall") for f in out)


def test_scoring_xfail_is_strict_and_crisis_cannot_be_xfail():
    known_gap = _result("insufficient_context", "grounded", faithful=True, xfail="gap")
    assert failures([known_gap]) == []  # expected failure tolerated
    fixed = _result("insufficient_context", "insufficient_context", xfail="gap")
    assert any("remove the marker" in f for f in failures([fixed]))
    excused_crisis = _result("crisis", "crisis", xfail="nope")
    assert any("can't be xfail" in f for f in failures([excused_crisis]))


def test_scoring_faithfulness_threshold():
    unfaithful = [_result("grounded", "grounded", faithful=False) for _ in range(3)]
    assert any(f.startswith("faithfulness") for f in failures(unfaithful))
