// Copyright 2026 Google LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     https://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

use garf::{
    self, Garf,
    garf::{Config, ExecutionContext, Workflow},
};
use std::path::Path;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error + Send + Sync + 'static>>
{
    let g = Garf::new("http://127.0.0.1:50051");
    let current_file = Path::new(file!());
    let dir = current_file.parent().unwrap_or_else(|| Path::new("."));
    let workflow_path = dir.join("test_workflow.yaml");
    let path_str = workflow_path.to_string_lossy().into_owned().into();
    match garf::read_from_file::<Workflow>(path_str) {
        Ok(file) => {
            g.execute_workflow(
                file,
                Config::default(),
                ExecutionContext::default(),
            )
            .await?;
        }
        Err(err) => {
            eprintln!("Error: {}", err);
        }
    };
    Ok(())
}
