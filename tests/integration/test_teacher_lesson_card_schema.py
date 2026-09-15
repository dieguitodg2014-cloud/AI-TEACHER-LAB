import json
import unittest
from pathlib import Path

from core.workflow.teacher_interface import plan_for_teacher, teacher_result_to_dict


class TeacherLessonCardSchemaTests(unittest.TestCase):
    def test_schema_declares_the_stable_teacher_contract(self):
        schema_path = Path(__file__).parents[2] / "data" / "schemas" / "teacher-lesson-card.schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))

        expected = (
            "status",
            "title",
            "level",
            "audience",
            "duration_minutes",
            "objective",
            "lesson",
            "activities",
            "assessment",
            "resource",
            "handoff",
            "errors",
        )

        self.assertEqual(tuple(schema["required"]), expected)
        self.assertEqual(tuple(schema["properties"]), expected)
        self.assertFalse(schema["additionalProperties"])

    def test_teacher_result_matches_schema_surface(self):
        result = plan_for_teacher(
            {
                "level": "A2",
                "audience": "adult ESL learners",
                "duration_minutes": 60,
                "objective": "Give recommendations using should and shouldn't.",
                "topic": "recommendations",
            }
        )
        payload = teacher_result_to_dict(result)

        schema_path = Path(__file__).parents[2] / "data" / "schemas" / "teacher-lesson-card.schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))

        self.assertEqual(tuple(payload), tuple(schema["properties"]))
        self.assertTrue(set(schema["required"]).issubset(payload))


if __name__ == "__main__":
    unittest.main()
