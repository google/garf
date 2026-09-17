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
    Garf,
    garf::{
        Config, ExecutionContext, QueryDefinition, QueryEntry, Workflow,
        WorkflowStep,
    },
};
use pbjson_types::{Struct, Value, value::Kind};
use std::collections::HashMap;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error + Send + Sync + 'static>>
{
    let g = Garf::new("http://127.0.0.1:50051");
    let mut fields = HashMap::new();
    fields.insert(
        "n_rows".to_string(),
        Value {
            kind: Some(Kind::NumberValue(10f64)),
        },
    );
    let workflow = Workflow {
        name: "test".to_string(),
        steps: vec![WorkflowStep {
            fetcher: "fake".to_string(),
            alias: "test".to_string(),
            fetcher_parameters: Some(Struct { fields }),
            queries: vec![QueryEntry {
                query: Some(QueryDefinition {
                    text: "SELECT metric.int AS field FROM fake".to_string(),
                    title: "test".to_string(),
                }),
            }],
            ..Default::default()
        }],
        ..Default::default()
    };
    let config = Config::default();
    let context = ExecutionContext::default();
    g.execute_workflow(workflow, config, context).await?;
    Ok(())
}
