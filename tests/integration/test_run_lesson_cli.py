import argparse
import unittest

from run_lesson import build_parser, build_request


class RunLessonCliTests(unittest.TestCase):
    def test_teacher_text_is_default_format(self):
        args = build_parser().parse_args(
            [
                "--objective",
                "Give recommendations using should and shouldn't.",
                "--level",
                "A1",
                "--audience",
                "adult ESL learners",
            ]
        )

        self.assertEqual(args.format, "teacher-text")

    def test_teacher_json_format_is_explicit(self):
        args = build_parser().parse_args(
            [
                "--request",
                "Create an A2 lesson about food.",
                "--format",
                "teacher",
            ]
        )

        self.assertEqual(args.format, "teacher")
        self.assertEqual(args.request, "Create an A2 lesson about food.")

    def test_internal_format_remains_available(self):
        args = build_parser().parse_args(
            [
                "--request",
                "Create an A2 lesson about food.",
                "--format",
                "internal",
            ]
        )

        self.assertEqual(args.format, "internal")

    def test_structured_request_preserves_optional_teacher_inputs(self):
        args = build_parser().parse_args(
            [
                "--objective",
                "Ask and answer questions about past experiences.",
                "--level",
                "A2",
                "--audience",
                "adult ESL learners",
                "--duration",
                "60",
                "--topic",
                "life experiences",
                "--group-size",
                "12",
            ]
        )

        request = build_request(args)

        self.assertEqual(request["level"], "A2")
        self.assertEqual(request["audience"], "adult ESL learners")
        self.assertEqual(request["duration_minutes"], 60)
        self.assertEqual(request["objective"], "Ask and answer questions about past experiences.")
        self.assertEqual(request["topic"], "life experiences")
        self.assertEqual(request["group_size"], 12)

    def test_objective_mode_requires_level_and_audience(self):
        args = argparse.Namespace(
            request=None,
            objective="Practice speaking.",
            level=None,
            audience="adult ESL learners",
            duration=60,
            topic="",
            group_size=None,
        )

        with self.assertRaisesRegex(ValueError, "--level and --audience"):
            build_request(args)


if __name__ == "__main__":
    unittest.main()
