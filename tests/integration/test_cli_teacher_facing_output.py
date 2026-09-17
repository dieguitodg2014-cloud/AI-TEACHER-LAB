from __future__ import annotations

from unittest.mock import patch

import run_lesson


def test_cli_uses_teacher_facing_output_boundary(capsys):
    with patch.object(run_lesson, "run_teacher_facing_lesson", return_value="<html>teacher card</html>") as runner:
        with patch.object(run_lesson, "build_request", return_value={"objective": "Talk about routines"}):
            with patch.object(run_lesson, "build_parser") as parser_builder:
                parser_builder.return_value.parse_args.return_value = object()
                assert run_lesson.main() == 0

    runner.assert_called_once_with({"objective": "Talk about routines"})
    assert capsys.readouterr().out.strip() == "<html>teacher card</html>"
