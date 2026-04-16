from utils.i18n import i18n


REQUIRED_KEYS = [
    "half_pipe_input_mode",
    "half_pipe_mode_help",
    "half_pipe_mode_coverage",
    "half_pipe_mode_turns",
    "half_pipe_pitch_label",
    "half_pipe_pitch_help",
    "half_pipe_turn_count_label",
    "half_pipe_turn_count_help",
    "half_pipe_coverage_label",
    "half_pipe_coverage_help",
    "half_pipe_basis_coverage",
    "half_pipe_basis_turns",
    "natural_convection_note",
    "conventional_jacket_note",
    "implied_half_pipe_coverage",
]


def test_i18n_contains_half_pipe_and_description_keys_for_both_languages():
    for lang in ["en", "ko"]:
        for key in REQUIRED_KEYS:
            assert key in i18n[lang]
            assert isinstance(i18n[lang][key], str)
            assert i18n[lang][key]
