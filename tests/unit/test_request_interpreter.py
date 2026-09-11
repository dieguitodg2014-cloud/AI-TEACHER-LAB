import unittest

from core.context.request_interpreter import interpret_request


class RequestInterpreterTests(unittest.TestCase):
    def test_extracts_explicit_lesson_request_fields(self):
        result = interpret_request(
            "Create an A2 lesson for 20 adult ESL learners, 90 minutes. "
            "Topic: Present Perfect. Objective: Discuss past experiences. "
            "Constraints: students struggle with questions; no extra homework."
        )

        self.assertEqual(result["level"], "A2")
        self.assertEqual(result["group_size"], 20)
        self.assertEqual(result["duration_minutes"], 90)
        self.assertEqual(result["audience"], "adult ESL learners")
        self.assertEqual(result["topic"], "Present Perfect")
        self.assertEqual(result["objective"], "Discuss past experiences.")
        self.assertEqual(
            result["constraints"],
            ["students struggle with questions", "no extra homework."],
        )

    def test_does_not_invent_missing_pedagogical_information(self):
        result = interpret_request("Create a lesson about English grammar.")

        self.assertNotIn("level", result)
        self.assertNotIn("audience", result)
        self.assertNotIn("duration_minutes", result)
        self.assertNotIn("objective", result)

    def test_preserves_structured_fields(self):
        request = {
            "request": "Create an A2 lesson for 90 minutes. Topic: Present Perfect.",
            "level": "B1",
            "objective": "Practice speaking.",
        }

        result = interpret_request(request)

        self.assertEqual(result["level"], "B1")
        self.assertEqual(result["objective"], "Practice speaking.")
        self.assertEqual(result["duration_minutes"], 90)
        self.assertEqual(result["topic"], "Present Perfect")

    def test_empty_request_returns_empty_structure(self):
        self.assertEqual(interpret_request(""), {})


if __name__ == "__main__":
    unittest.main()
