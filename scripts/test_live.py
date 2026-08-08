"""Live end-to-end test of the interview agent with real LLM."""

import asyncio
import os

# Ensure model is set correctly
os.environ["LLM_MODEL"] = "llama-3.3-70b-versatile"

# Reset config singleton before anything loads
from app.core import config as cfg_module
cfg_module._settings = None

from app.core.config import get_settings
from app.llm.factory import create_llm_provider
from app.services.curriculum_service import CurriculumService
from app.services.candidate_service import CandidateService, CandidateAnalysis
from app.services.question_service import QuestionService
from app.services.evaluation_service import EvaluationService
from app.services.interview_service import InterviewService
from app.memory.repositories import InMemoryInterviewRepository, InMemoryFeedbackRepository


async def main():
    settings = get_settings()
    print(f"Provider: {settings.llm_provider}")
    print(f"Model: {settings.llm_model}")
    print(f"Key: {settings.llm_api_key[:10]}...")
    print()

    # Create services
    llm = create_llm_provider()
    curriculum_service = CurriculumService()
    candidate_service = CandidateService()
    question_service = QuestionService()
    evaluation_service = EvaluationService(llm=llm)
    interview_repo = InMemoryInterviewRepository()
    feedback_repo = InMemoryFeedbackRepository()

    await curriculum_service.load()
    await candidate_service.load()

    service = InterviewService(
        llm=llm,
        interview_repo=interview_repo,
        feedback_repo=feedback_repo,
        curriculum_service=curriculum_service,
        candidate_service=candidate_service,
        question_service=question_service,
        evaluation_service=evaluation_service,
    )

    # Start interview
    print("=" * 60)
    print("STARTING INTERVIEW (candidate_001 - Alex Chen)")
    print("=" * 60)

    try:
        result = await service.start_interview("candidate_001")
        print(f"Interview ID: {result['interview_id']}")
        print(f"\nInterviewer: {result['message']}")
        print()
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return

    iid = result["interview_id"]

    # Answer 1
    print("-" * 60)
    answer1 = (
        "I built a RAG system using LangChain and ChromaDB. The architecture had a "
        "document ingestion pipeline with recursive text splitting at 512 tokens with "
        "50 token overlap. I used OpenAI ada-002 for embeddings stored in ChromaDB. "
        "For retrieval I used similarity search with top-k of 5 chunks, then passed "
        "them as context to GPT-4 for generation. One decision I'd change is the "
        "chunking strategy - I'd use semantic chunking instead of fixed-size splits."
    )
    print(f"Candidate: {answer1[:100]}...")
    print()

    try:
        result2 = await service.submit_answer(iid, answer1)
        print(f"Turn: {result2['turn']} | Days: {result2['curriculum_days_covered']}")
        print(f"\nInterviewer: {result2['message']}")
        print()
    except Exception as e:
        print(f"ERROR on answer 1: {e}")
        import traceback
        traceback.print_exc()
        return

    # Answer 2
    print("-" * 60)
    answer2 = (
        "To diagnose retrieval quality, I would first look at the retrieved chunks "
        "manually for a sample of queries. I'd compute metrics like precision@k and "
        "recall. If chunks are semantically similar but irrelevant, the issue is likely "
        "in chunking boundaries or the embedding model not capturing domain-specific "
        "semantics. I'd consider a reranking step with a cross-encoder."
    )
    print(f"Candidate: {answer2[:100]}...")
    print()

    try:
        result3 = await service.submit_answer(iid, answer2)
        print(f"Turn: {result3['turn']} | Days: {result3['curriculum_days_covered']}")
        print(f"\nInterviewer: {result3['message']}")
    except Exception as e:
        print(f"ERROR on answer 2: {e}")
        import traceback
        traceback.print_exc()
        return

    print()
    print("=" * 60)
    print("LIVE TEST PASSED - Interview agent working with Groq!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
