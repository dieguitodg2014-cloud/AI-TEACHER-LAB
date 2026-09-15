import unittest

from core.foundation.models import TaskPacket


class TaskPacketImmutabilityTests(unittest.TestCase):
    def _task(self, **overrides):
        values = {
            "task_id": "task-immutability",
            "task_type": "RESOURCE_PRODUCTION",
            "objective": "Create a short listening resource.",
            "level": "A2",
            "required_output": "audio",
            "constraints": ["English", "Use source references"],
            "quality_criteria": ["Support the objective.", "Match A2."],
            "input_materials": ["lesson-notes"],
        }
        values.update(overrides)
        return TaskPacket(**values)

    def test_collections_are_normalized_to_tuples(self):
        task = self._task()

        self.assertIsInstance(task.constraints, tuple)
        self.assertIsInstance(task.quality_criteria, tuple)
        self.assertIsInstance(task.input_materials, tuple)

    def test_source_lists_cannot_be_mutated_through_original_inputs(self):
        constraints = ["English"]
        criteria = ["Support the objective."]
        materials = ["notes"]

        task = self._task(
            constraints=constraints,
            quality_criteria=criteria,
            input_materials=materials,
        )

        constraints.append("new constraint")
        criteria.append("new criterion")
        materials.append("new material")

        self.assertEqual(task.constraints, ("English",))
        self.assertEqual(task.quality_criteria, ("Support the objective.",))
        self.assertEqual(task.input_materials, ("notes",))

    def test_frozen_packet_rejects_field_reassignment(self):
        task = self._task()

        with self.assertRaises((AttributeError, TypeError)):
            task.objective = "Changed objective"

    def test_collection_items_cannot_be_appended(self):
        task = self._task()

        with self.assertRaises(AttributeError):
            task.constraints.append("new constraint")


if __name__ == "__main__":
    unittest.main()
