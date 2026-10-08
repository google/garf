# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Module for writing GarfReport to a file."""

import os
import pathlib
from typing import Union

from garf.io import exceptions
from garf.io.telemetry import tracer
from garf.io.writers.abs_writer import AbsWriter


class FileWriter(AbsWriter):
  """Writes Garf Report to a local or remote file.

  Attributes:
      destination_folder: Destination where output file is stored.
  """

  def __init__(
    self,
    destination_folder: Union[str, os.PathLike[str], pathlib.Path] = os.getenv(
      'GARF_DESTINATION_FOLDER', str(pathlib.Path.cwd())
    ),
    **kwargs: str,
  ) -> None:
    """Initializes FileWriter based on destination folder."""
    super().__init__(**kwargs)
    if allowed_folders := os.getenv('GARF_ALLOWED_FOLDERS'):
      allowed_folders = allowed_folders.split(',')
      if not any(
        allowed_destination in str(destination_folder)
        for allowed_destination in allowed_folders
      ):
        raise exceptions.GarfIoError(
          f'Destination folder {destination_folder} not supported.'
        )

    self.destination_folder = str(destination_folder)

  @tracer.start_as_current_span('file.create_dir')
  def create_dir(self) -> None:
    """Creates folders if needed or destination is not remote."""
    if (
      not pathlib.Path(self.destination_folder).is_dir()
      and '://' not in self.destination_folder
    ):
      pathlib.Path(self.destination_folder).mkdir(parents=True)

  def write(self) -> None:
    return
