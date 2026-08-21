# Copyright 2026 Google LLC
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

import pydantic


class Label(pydantic.BaseModel):
  name: str = pydantic.Field(min_length=1, max_length=80)
  description: str | None = pydantic.Field(
    default=None, min_length=1, max_length=200
  )
  color: str | None = pydantic.Field(
    default=None, pattern=r'^#([a-fA-F0-9]{6}|[a-fA-F0-9]{3})$'
  )
  label_id: int | None = None

  def to_operation(self, client):
    operation = client.get_type('LabelOperation')
    label = operation.create
    label.name = self.name
    if self.description:
      label.text_label.description = self.description
    if self.color:
      label.text_label.background_color = self.color
    return operation
