import pytest

from cv_review_agent.schemas import JobTemplate
from cv_review_agent.storage import validate_template_limit


def make_template(index: int) -> JobTemplate:
    return JobTemplate(
        id=f"job-{index}",
        title=f"Role {index}",
        required_conditions=["Python"],
        bonus_conditions=[],
        responsibilities=[],
        minimum_years=2,
        disqualifiers=[],
        notes="",
    )


def test_validate_template_limit_allows_one_to_three_templates():
    templates = [make_template(1), make_template(2), make_template(3)]

    validate_template_limit(templates)


def test_validate_template_limit_rejects_zero_or_more_than_three_templates():
    with pytest.raises(ValueError, match="1 to 3"):
        validate_template_limit([])

    with pytest.raises(ValueError, match="1 to 3"):
        validate_template_limit([make_template(i) for i in range(4)])
