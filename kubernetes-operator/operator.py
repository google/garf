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
from typing import Final

import kopf
import kubernetes
import pydantic

GARF_CLI_IMAGE: Final[str] = 'ghcr.io/google/garf-rust-sdk:latest'


class ServerInfo(pydantic.BaseModel):
  url: str | None = None
  server_type: str = None

  def __bool__(self) -> bool:
    return bool(self.url and self.server_type)


class GarfWorkflowCronJob(pydantic.BaseModel):
  config = pydantic.ConfigDict(extra='allow')
  workflow_path: str
  config_path: str | None = None
  server: ServerInfo = ServerInfo()

  @property
  def command(self) -> str:
    cli_args = ['grf workflow run', f'-f {self.workflow_path}']

    if server := self.server_info:
      cli_args.append(f'--server-url={server.url} --server-type={server.type}')

    if self.config_path:
      cli_args.append(f'--config {self.config_path}')
    return ' \\\n '.join(cli_args)

  @property
  def job_template(
    self,
  ) -> kubernetes.client.models.v1_job_template_spec.V1JobTemplateSpec:
    return kubernetes.client.models.v1_job_template_spec.V1JobTemplateSpec(
      spec={
        'template': {
          'containers': [
            {
              'name': 'grf',
              'image': GARF_CLI_IMAGE,
              'command': ['/bin/sh', '-c'],
              'args': self.command,
            }
          ],
          'restartPolicy': 'OnFailure',
        }
      }
    )


def _build_cron_job(
  name: str, namespace: str | None, spec: kopf.Spec
) -> kubernetes.client.V1CronJob:
  workflow_cronjob = GarfWorkflowCronJob(**spec)
  return kubernetes.client.V1CronJob(
    api_version='batch/v1',
    kind='CronJob',
    metadata={
      'name': name,
      'namespace': namespace,
    },
    spec={
      'schedule': spec.get('schedule'),
      'jobTemplate': workflow_cronjob.job_template,
    },
  )


@kopf.on.create('garf.io', 'v1', 'garfcronjobs')
def create(
  spec: kopf.Spec,
  name: str,
  namespace: str | None,
  logger: kopf.Logger,
  **kwargs,
) -> None:
  cronjob = kubernetes.client.V1CronJob()
  kopf.adopt(cronjob)
  batch_v1 = kubernetes.client.BatchV1Api()
  try:
    batch_v1.create_namespaced_cron_job(namespace=namespace, body=cronjob)
    logger.info(f'Successfully created GarfCronJob: {namespace}/{name}')
  except kubernetes.client.exceptions.ApiException as e:
    if e.status == 409:
      batch_v1.patch_namespaced_cron_job_status(
        name=name, namespace=namespace, body=cronjob
      )
      logger.info(f'GarfCronJob exists, patching: {namespace}/{name}')
    else:
      raise kopf.PermanentError(f'Failed to create GarfCronJob: {e}')
