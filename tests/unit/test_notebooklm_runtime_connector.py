import unittest

from tools.connectors.notebooklm import (
    NotebookLMConnectorError,
    create_notebooklm_generator,
)


class NotebookLMRuntimeConnectorTests(unittest.TestCase):
    def test_factory_returns_callable_with_explicit_unconfigured_boundary(self):
        generator = create_notebooklm_generator()

        self.assertTrue(callable(generator))
        with self.assertRaisesRegex(
            NotebookLMConnectorError,
            "NOTEBOOKLM_CONNECTOR_NOT_CONFIGURED",
        ):
            generator({"provider": "notebooklm", "task": {"task_id": "task-1"}})

    def test_invalid_payload_is_rejected_before_external_execution(self):
        generator = create_notebooklm_generator()

        with self.assertRaisesRegex(
            NotebookLMConnectorError,
            "NOTEBOOKLM_INVALID_REQUEST",
        ):
            generator([])


if __name__ == "__main__":
    unittest.main()
