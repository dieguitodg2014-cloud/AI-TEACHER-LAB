import unittest

from core.orchestration.provider_capability_contract import (
    SUPPORTED_PROVIDER_CAPABILITIES,
    provider_supports_capabilities,
    validate_provider_capabilities,
)


class ProviderCapabilityContractTests(unittest.TestCase):
    def test_valid_capabilities_are_accepted(self):
        self.assertEqual(validate_provider_capabilities(["lesson_generation"]), [])
        self.assertEqual(validate_provider_capabilities(["resource_generation"]), [])

    def test_non_collection_is_rejected(self):
        self.assertEqual(
            validate_provider_capabilities("lesson_generation"),
            ["PROVIDER_CAPABILITIES_NOT_COLLECTION"],
        )

    def test_unknown_capability_is_rejected(self):
        self.assertEqual(
            validate_provider_capabilities(["visual_generation"]),
            ["PROVIDER_CAPABILITY_UNSUPPORTED:visual_generation"],
        )

    def test_invalid_capability_type_is_rejected(self):
        self.assertEqual(
            validate_provider_capabilities(["lesson_generation", 123]),
            ["PROVIDER_CAPABILITY_INVALID_TYPE"],
        )

    def test_required_capabilities_must_be_declared(self):
        self.assertTrue(
            provider_supports_capabilities(
                ["lesson_generation"], {"lesson_generation"}
            )
        )
        self.assertFalse(
            provider_supports_capabilities(
                ["lesson_generation"], {"resource_generation"}
            )
        )

    def test_supported_capabilities_are_explicit(self):
        self.assertEqual(
            SUPPORTED_PROVIDER_CAPABILITIES,
            frozenset({"lesson_generation", "resource_generation"}),
        )


if __name__ == "__main__":
    unittest.main()
