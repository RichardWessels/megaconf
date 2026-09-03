import pytest

from megaconf.exceptions import UnsupportedConfigFileError
from megaconf._inputs import load_data_from_file


def test_unsupported_config_file_raises_domain_exception(tmp_path):
    file_path = tmp_path / "config.toml"

    with pytest.raises(UnsupportedConfigFileError, match="File must end"):
        load_data_from_file(file_path)
