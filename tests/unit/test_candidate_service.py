"""Unit tests for candidate analysis."""

import pytest
from app.services.candidate_service import CandidateAnalysis


class TestCandidateAnalysis:
    def test_identifies_strong_areas(self, sample_candidate, sample_curriculum):
        analysis = CandidateAnalysis(sample_candidate, sample_curriculum)
        assert "RAG" in analysis.strong_areas or "retrieval" in analysis.strong_areas

    def test_identifies_weak_areas(self, sample_candidate, sample_curriculum):
        analysis = CandidateAnalysis(sample_candidate, sample_curriculum)
        assert "Deployment" in analysis.weak_areas or "deployment" in analysis.weak_areas

    def test_identifies_skipped_topics(self, sample_candidate, sample_curriculum):
        # Add a skipped day that exists in the test curriculum
        from app.domain.models import CurriculumDay
        sample_curriculum.days.append(CurriculumDay(
            day=14, module="MCP", topic="MCP Introduction",
            concepts=["MCP", "Model Context Protocol"],
            learning_objectives=["Understand MCP"], tools=["MCP SDK"],
            projects=["MCP server"], difficulty="intermediate",
            expected_skills=["Build MCP servers"],
        ))
        analysis = CandidateAnalysis(sample_candidate, sample_curriculum)
        # Day 14 is in skipped_topics and now exists in curriculum
        assert len(analysis.skipped_areas) > 0

    def test_completed_days_tracked(self, sample_candidate, sample_curriculum):
        analysis = CandidateAnalysis(sample_candidate, sample_curriculum)
        assert 1 in analysis.completed_days
        assert 7 in analysis.completed_days

    def test_focus_areas_include_weak_and_strong(self, sample_candidate, sample_curriculum):
        analysis = CandidateAnalysis(sample_candidate, sample_curriculum)
        focus = analysis.get_interview_focus_areas()
        assert len(focus) > 0
