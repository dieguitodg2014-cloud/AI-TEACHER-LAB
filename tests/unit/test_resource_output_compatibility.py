import unittest

from core.orchestration.resource_output_compatibility import (
    provider_supports_resource_output,
    resource_output_capability,
)


class ResourceOutputCompatibilityTests(unittest.TestCase):
    def test_output_type_maps_to_stable_execution_capability(self):
        self.assertEqual(resource_output_capability("audio"), "resource_output:audio")
        self.assertEqual(
            resource_output_capability("video or visual"),
            "resource_output:video_or_visual",
        )

    def test_provider_must_explicitly_declare_required_output(self):
        self.assertTrue(
            provider_supports_resource_output(
                {"resource_generation", "resource_output:audio"}, "audio"
            )
        )
        self.assertFalse(
            provider_supports_resource_output(
                {"resource_generation", "resource_output:video"}, "audio"
            )
        )
        self.assertFalse(
            provider_supports_resource_output({"resource_generation"}, "audio")
        )

    def test_blank_required_output_is_not_compatible(self):
        self.assertEqual(resource_output_capability("   "), "")
        self.assertFalse(
            provider_supports_resource_output(
                {"resource_generation", "resource_output:audio"}, "   "
            )
        )


if __name__ == "__main__":
    unittest.main()
