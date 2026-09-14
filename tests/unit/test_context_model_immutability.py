import unittest

from core.foundation.models import Context


class ContextModelImmutabilityTests(unittest.TestCase):
    def test_sequence_fields_are_normalized_to_tuples(self):
        context = Context(
            context_id="ctx-immutable-001",
            level="A2",
            audience="adult learners",
            duration_minutes=60,
            objective="Discuss everyday routines.",
            constraints=["pair work"],
            prior_knowledge=["present simple"],
            technology=["projector"],
        )

        self.assertEqual(context.constraints, ("pair work",))
        self.assertEqual(context.prior_knowledge, ("present simple",))
        self.assertEqual(context.technology, ("projector",))

    def test_sequence_fields_cannot_be_mutated(self):
        context = Context(
            context_id="ctx-immutable-002",
            level="A1",
            audience="learners",
            duration_minutes=45,
            objective="Introduce yourself.",
            constraints=["simple language"],
            prior_knowledge=["basic greetings"],
            technology=["none"],
        )

        with self.assertRaises(AttributeError):
            context.constraints.append("new constraint")
        with self.assertRaises(AttributeError):
            context.prior_knowledge.append("new knowledge")
        with self.assertRaises(AttributeError):
            context.technology.append("new tool")


if __name__ == "__main__":
    unittest.main()
