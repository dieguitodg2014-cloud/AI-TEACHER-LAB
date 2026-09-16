import unittest
from dataclasses import FrozenInstanceError, asdict

from core.foundation.models import TaskPacket


class TaskPacketImmutabilityTests(unittest.TestCase):
    def _packet(self) -> TaskPacket:
        return TaskPacket(
            task_id="immutability-test",
            task_type="RESOURCE_PRODUCTION",
            objective="Create a short listening resource.",
            level="A2",
            required_output="audio",
            constraints=["English", "90 seconds"],
            quality_criteria=["Match A2", "Support the objective"],
            input_materials=["teacher_notes"],
        )

    def test_contract_collections_are_tuples(self):
        packet = self._packet()

        self.assertIsInstance(packet.constraints, tuple)
        self.assertIsInstance(packet.quality_criteria, tuple)
        self.assertIsInstance(packet.input_materials, tuple)

    def test_reassignment_is_rejected(self):
        packet = self._packet()

        with self.assertRaises(FrozenInstanceError):
            packet.constraints = ("changed",)

    def test_nested_collection_mutation_is_rejected(self):
        packet = self._packet()

        with self.assertRaises(AttributeError):
            packet.constraints.append("changed")
        with self.assertRaises(AttributeError):
            packet.quality_criteria.append("changed")
        with self.assertRaises(AttributeError):
            packet.input_materials.append("changed")

    def test_constructor_copies_mutable_inputs(self):
        constraints = ["English"]
        quality_criteria = ["Match A2"]
        input_materials = ["teacher_notes"]

        packet = TaskPacket(
            task_id="copy-test",
            task_type="RESOURCE_PRODUCTION",
            objective="Create a resource.",
            level="A2",
            required_output="worksheet",
            constraints=constraints,
            quality_criteria=quality_criteria,
            input_materials=input_materials,
        )

        constraints.append("mutated")
        quality_criteria.append("mutated")
        input_materials.append("mutated")

        self.assertEqual(packet.constraints, ("English",))
        self.assertEqual(packet.quality_criteria, ("Match A2",))
        self.assertEqual(packet.input_materials, ("teacher_notes",))

    def test_asdict_remains_serializable_as_json_arrays(self):
        packet = self._packet()
        data = asdict(packet)

        self.assertEqual(data["constraints"], ("English", "90 seconds"))
        self.assertEqual(data["quality_criteria"], ("Match A2", "Support the objective"))
        self.assertEqual(data["input_materials"], ("teacher_notes",))


if __name__ == "__main__":
    unittest.main()
