import pytest

from sumtraits import cli


def test_help_renders_without_importing_workflow(capsys):
    with pytest.raises(SystemExit) as exc_info:
        cli.main(["--help"])

    assert exc_info.value.code == 0
    assert "Summarize traits from a taxonomic profile." in capsys.readouterr().out


def test_invalid_taxonomic_profile_type_exits_with_argparse_error(capsys):
    with pytest.raises(SystemExit) as exc_info:
        cli.main(
            [
                "profile.tsv",
                "--taxonomic-profile-type",
                "invalid",
                "--taxonomy-type",
                "ncbi",
                "--output-dir",
                "out",
            ]
        )

    assert exc_info.value.code == 2
    assert "invalid choice" in capsys.readouterr().err


def test_main_passes_parsed_arguments_to_workflow(monkeypatch):
    calls = []

    def fake_run_workflow(*args):
        calls.append(args)
        return 0

    monkeypatch.setattr(cli, "_run_workflow", fake_run_workflow)

    exit_code = cli.main(
        [
            "profile.tsv",
            "--taxonomic-profile-type",
            "bracken",
            "--taxonomy-type",
            "ncbi",
            "--output-dir",
            "out",
            "--exclude-prediction-based",
        ]
    )

    assert exit_code == 0
    assert calls == [("profile.tsv", "bracken", "ncbi", True, "out")]


def test_main_reports_runtime_errors_without_traceback(monkeypatch, capsys):
    def fake_run_workflow(*args):
        raise RuntimeError("bad profile")

    monkeypatch.setattr(cli, "_run_workflow", fake_run_workflow)

    exit_code = cli.main(
        [
            "profile.tsv",
            "--taxonomic-profile-type",
            "bracken",
            "--taxonomy-type",
            "ncbi",
            "--output-dir",
            "out",
        ]
    )

    stderr = capsys.readouterr().err
    assert exit_code == 1
    assert "sumtraits failed: bad profile" in stderr
    assert "Traceback" not in stderr


def test_main_reports_runtime_errors_with_traceback_when_verbose(monkeypatch, capsys):
    def fake_run_workflow(*args):
        raise RuntimeError("bad profile")

    monkeypatch.setattr(cli, "_run_workflow", fake_run_workflow)

    exit_code = cli.main(
        [
            "profile.tsv",
            "--taxonomic-profile-type",
            "bracken",
            "--taxonomy-type",
            "ncbi",
            "--output-dir",
            "out",
            "--verbose",
        ]
    )

    stderr = capsys.readouterr().err
    assert exit_code == 1
    assert "sumtraits failed: bad profile" in stderr
    assert "Traceback" in stderr
