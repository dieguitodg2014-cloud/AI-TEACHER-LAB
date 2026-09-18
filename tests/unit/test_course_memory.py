import json
import tempfile
import unittest
from pathlib import Path

from core.memory.course_memory import CourseMemory, InMemoryCourseMemoryStore, JsonCourseMemoryStore


class CourseMemoryTests(unittest.TestCase):
    def test_new_course_starts_empty(self):
        memory = CourseMemory("course-1")
        self.assertEqual(memory.session_count, 0)
        self.assertEqual(memory.next_session_number, 1)
        self.assertEqual(memory.completed_lesson_ids, ())

    def test_completed_lesson_creates_new_immutable_snapshot(self):
        before = CourseMemory("course-1")
        after = before.record_completed_lesson(
            "lesson-1",
            topic="Daily routines",
            level="A1",
            objective="Describe daily routines.",
            duration_minutes=60,
        )

        self.assertEqual(before.session_count, 0)
        self.assertEqual(after.session_count, 1)
        self.assertEqual(after.completed_lesson_ids, ("lesson-1",))
        self.assertEqual(after.completed_topics, ("Daily routines",))
        self.assertEqual(after.last_level, "A1")
        self.assertEqual(after.next_session_number, 2)
        self.assertIsInstance(after.completed_lesson_ids, tuple)

    def test_duplicate_completion_is_idempotent(self):
        memory = CourseMemory("course-1").record_completed_lesson("lesson-1", topic="A")
        retry = memory.record_completed_lesson("lesson-1", topic="B", level="B1")
        self.assertEqual(retry, memory)

    def test_in_memory_store_preserves_state_across_lessons(self):
        store = InMemoryCourseMemoryStore()
        first = store.get("course-1").record_completed_lesson("lesson-1", topic="Introductions")
        store.save(first)
        second = store.get("course-1")
        self.assertEqual(second.session_count, 1)
        self.assertEqual(second.last_topic, "Introductions")

    def test_json_store_round_trip_is_durable(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "course-memory.json"
            store = JsonCourseMemoryStore(path)
            memory = CourseMemory("course-1").record_completed_lesson(
                "lesson-1", topic="Present perfect", level="A2"
            )
            store.save(memory)

            restored = JsonCourseMemoryStore(path).get("course-1")
            self.assertEqual(restored, memory)
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(payload["course-1"]["session_count"], 1)

    def test_invalid_session_count_is_rejected(self):
        with self.assertRaises(ValueError):
            CourseMemory("course-1", session_count=1)


if __name__ == "__main__":
    unittest.main()
