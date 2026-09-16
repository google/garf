mod grf;
mod telemetry;
use crate::grf::garf::{
    Config, ExecutionContext, QueryDefinition, QueryEntry, Workflow,
    WorkflowStep,
};
use grf::Garf;
use prost_types::{Struct, Value, value::Kind};

use std::collections::{BTreeMap, HashMap};

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error + Send + Sync + 'static>>
{
    let otel_guard = match telemetry::setup_otel() {
        Ok(guard) => guard,
        Err(err) => {
            panic!("Couldn't start Otel: {0}", err);
        }
    };
    let _ = telemetry::create_span("garf-rust", "run");
    let g = Garf::new("http://127.0.0.1:50051");

    g.info().await?;
    g.version().await?;
    g.fetchers().await?;
    g.executors().await?;

    g.execute("SELECT metric.int AS field FROM fake", "test")
        .await?;

    let mut batches = HashMap::new();
    batches.insert("test1", "SELECT metric.int AS field FROM fake");
    batches.insert("test2", "SELECT metric.int AS field FROM fake");
    batches.insert("test3", "SELECT metric.int AS field FROM fake");
    g.execute_batch(batches).await?;

    let mut fields = BTreeMap::new();
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

    otel_guard.shutdown();
    Ok(())
}
