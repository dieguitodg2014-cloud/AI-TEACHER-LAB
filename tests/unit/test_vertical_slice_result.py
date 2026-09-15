import unittest

from core.workflow.vertical_slice import VerticalSliceResult


class VerticalSliceResultImmutabilityTests(unittest.TestCase):
    def test_result_collections_are_normalized_to_tuples(self):
        result = VerticalSliceResult(
            status="PLANNED",
            context=None,
            level_decision=None,
            learning_plan=None,
            assessment_decision=None,
            resource_decision=None,
            resource_task=None,
            resource_tool=None,
            resource_handoff=None,
            resource_validation=None,
            generation=None,
            missing=["objective"],
            errors=["example-error"],
        )

        self.assertEqual(result.missing, ("objective",))
        self.assertEqual(result.errors, ("example-error",))
        with self.assertRaises(AttributeError):
            result.missing.append("level")
        with self.assertRaises(AttributeError):
            result.errors.append("another-error")


if __name__ == "__main__":
    unittest.main()
