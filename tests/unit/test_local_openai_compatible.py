
        sent = json.loads(mocked.call_args.args[0].data.decode("utf-8"))
        self.assertEqual(sent["max_tokens"], DEFAULT_MAX_TOKENS)

    def test_timeout_environment_override_is_used(self):
        with patch.dict("os.environ", {"AI_TEACHER_LAB_PROVIDER_TIMEOUT_SECONDS": "300"}, clear=False):
            generator = create_local_openai_compatible_generator(base_url="http://test")
            with patch("tools.connectors.local_openai_compatible.request.urlopen", return_value=FakeResponse({
                "choices": [{"message": {"content": "{}"}}]
            })) as mocked:
                generator({"level": "A2"}, [])

        self.assertEqual(mocked.call_args.kwargs["timeout"], 300)

    def test_timeout_is_controlled(self):
        generator = create_local_openai_compatible_generator(base_url="http://test")

        with patch(
            "tools.connectors.local_openai_compatible.request.urlopen",
            side_effect=TimeoutError("timed out"),