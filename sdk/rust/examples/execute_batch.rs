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

use garf::Garf;
use std::collections::HashMap;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error + Send + Sync + 'static>>
{
    let g = Garf::new("http://127.0.0.1:50051");
    let mut batches = HashMap::new();
    batches.insert("test1", "SELECT metric.int AS field FROM fake");
    batches.insert("test2", "SELECT metric.int AS field FROM fake");
    batches.insert("test3", "SELECT metric.int AS field FROM fake");
    g.execute_batch(batches).await?;
    Ok(())
}
