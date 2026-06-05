# Spec: DATA-012
# Schema: KnowledgeArticle
# File: specs/data/KnowledgeArticle.schema.json
# API Refs: (none — internal knowledge base)
# Description: A curated knowledge base article for patient education and navigator reference.

"""
Schema validation tests for the KnowledgeArticle entity.
@spec DATA-012
@file specs/data/KnowledgeArticle.schema.json
"""

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, ValidationError

SCHEMAS_DIR = Path(__file__).resolve().parents[4] / "specs" / "data"
SCHEMA_FILE = "KnowledgeArticle.schema.json"


@pytest.fixture
def article_schema():
    """Load the KnowledgeArticle JSON Schema."""
    with open(SCHEMAS_DIR / SCHEMA_FILE, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def validator(article_schema):
    """Create a Draft202012Validator for the KnowledgeArticle schema."""
    return Draft202012Validator(article_schema)


@pytest.fixture
def valid_article_instance():
    """Return the first example from the schema's examples array."""
    return {
        "id": "440e8400-e29b-41d4-a716-446655440014",
        "title": "Understanding Oral Cancer Treatment",
        "content": "# Understanding Oral Cancer Treatment\n\nOral cancer treatment depends on the stage and location...",
        "category": "cancer-care",
        "tags": ["oral-cancer", "treatment", "surgery", "radiation"],
        "language": "en",
        "source": "National Cancer Institute",
        "isPublished": True,
        "createdBy": "660e8400-e29b-41d4-a716-446655440001",
        "createdAt": "2026-06-04T10:00:00.000Z",
        "updatedAt": "2026-06-04T10:00:00.000Z",
    }


@pytest.mark.spec("DATA-012")
class TestKnowledgeArticleSchema:
    """Validation tests for KnowledgeArticle.schema.json (DATA-012)."""

    def test_valid_complete_instance(self, validator, valid_article_instance):
        """
        Scenario: DATA-012-1
        A complete KnowledgeArticle instance should pass validation.
        """
        result = validator.validate(valid_article_instance)
        assert result is None

    def test_missing_required_fields(self, validator):
        """
        Scenario: DATA-012-2
        An empty dict should fail because required fields are missing.
        Required: id, title, content, language, isPublished, createdAt, updatedAt.
        """
        with pytest.raises(ValidationError):
            validator.validate({})
        errors = list(validator.iter_errors({}))
        assert len(errors) >= 7

    def test_additional_properties_rejected(self, validator, valid_article_instance):
        """
        Scenario: DATA-012-3
        Extra fields should be rejected (additionalProperties: false).
        """
        instance = {**valid_article_instance, "viewCount": 150}
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(instance)
        assert "additional" in str(exc_info.value).lower() or "extra" in str(exc_info.value).lower()

    def test_field_type_validation(self, validator, valid_article_instance):
        """
        Scenario: DATA-012-4
        Wrong types should fail validation.
        - title (string) given as integer
        - content (string) given as array
        - language (string) given as boolean
        - isPublished (boolean) given as string
        - tags (array) given as string
        """
        wrong_title = {**valid_article_instance, "title": 12345}
        with pytest.raises(ValidationError):
            validator.validate(wrong_title)

        wrong_content = {**valid_article_instance, "content": ["markdown"]}
        with pytest.raises(ValidationError):
            validator.validate(wrong_content)

        wrong_lang = {**valid_article_instance, "language": True}
        with pytest.raises(ValidationError):
            validator.validate(wrong_lang)

        wrong_pub = {**valid_article_instance, "isPublished": "yes"}
        with pytest.raises(ValidationError):
            validator.validate(wrong_pub)

        wrong_tags = {**valid_article_instance, "tags": "oral-cancer"}
        with pytest.raises(ValidationError):
            validator.validate(wrong_tags)

    def test_field_constraints(self, validator, valid_article_instance):
        """
        Scenario: DATA-012-5
        Test enum, string length, and array constraints.
        - language: enum [en, ta]
        - title: minLength 1, maxLength 500
        - content: minLength 1, maxLength 100000
        - category: maxLength 100
        - tags: maxItems 20, items maxLength 64, uniqueItems true
        """
        # invalid language
        bad_lang = {**valid_article_instance, "language": "fr"}
        with pytest.raises(ValidationError):
            validator.validate(bad_lang)

        # empty title
        empty_title = {**valid_article_instance, "title": ""}
        with pytest.raises(ValidationError):
            validator.validate(empty_title)

        # title too long
        long_title = {**valid_article_instance, "title": "x" * 501}
        with pytest.raises(ValidationError):
            validator.validate(long_title)

        # content too long
        long_content = {**valid_article_instance, "content": "x" * 100001}
        with pytest.raises(ValidationError):
            validator.validate(long_content)

        # tags with too many items
        many_tags = [f"tag-{i}" for i in range(21)]
        huge_tags = {**valid_article_instance, "tags": many_tags}
        with pytest.raises(ValidationError):
            validator.validate(huge_tags)

        # tags with duplicate items
        dup_tags = {**valid_article_instance, "tags": ["oral-cancer", "oral-cancer"]}
        with pytest.raises(ValidationError):
            validator.validate(dup_tags)

        # category too long
        long_cat = {**valid_article_instance, "category": "x" * 101}
        with pytest.raises(ValidationError):
            validator.validate(long_cat)

    def test_nullable_fields_accept_null(self, validator, valid_article_instance):
        """
        Scenario: DATA-012-6
        Nullable fields should accept null.
        - category, tags, source, createdBy are nullable.
        """
        instance = {
            **valid_article_instance,
            "category": None,
            "tags": None,
            "source": None,
            "createdBy": None,
        }
        result = validator.validate(instance)
        assert result is None

    def test_uuid_format_validation(self, validator, valid_article_instance):
        """
        Scenario: DATA-012-7
        UUID fields should accept valid UUID format.
        Fields: id, createdBy.
        """
        valid = {
            **valid_article_instance,
            "id": "440e8400-e29b-41d4-a716-446655440014",
            "createdBy": "660e8400-e29b-41d4-a716-446655440001",
        }
        result = validator.validate(valid)
        assert result is None
