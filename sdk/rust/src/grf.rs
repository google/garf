pub mod garf {
    tonic::include_proto!("garf");
}
use crate::telemetry;
use garf::garf_service_client::GarfServiceClient;
use garf::{Config, ExecutionContext, Workflow};
use opentelemetry::{KeyValue, trace::TraceContextExt};
use prost_types::{Struct, Value, value::Kind};
use serde_json;
use std::collections::{BTreeMap, HashMap};

type GarfResult =
    Result<(), Box<dyn std::error::Error + Send + Sync + 'static>>;

pub struct Garf {
    pub endpoint: String,
}

impl Garf {
    pub fn new(endpoint: &str) -> Self {
        Garf {
            endpoint: endpoint.to_string(),
        }
    }

    async fn connect_client(
        &self,
    ) -> Result<
        GarfServiceClient<tonic::transport::Channel>,
        tonic::transport::Error,
    > {
        GarfServiceClient::connect(self.endpoint.clone()).await
    }

    pub async fn version(&self) -> GarfResult {
        let cx = telemetry::create_span("garf-rust", "version");
        let mut client = self.connect_client().await?;
        let req = telemetry::create_propagated_request(&cx, ());
        let response = client.get_version(req).await;
        let span = cx.span();
        let _ = match response {
            Ok(res) => {
                let version = &res.get_ref().version;
                span.set_attribute(KeyValue::new(
                    "garf.version",
                    version.clone(),
                ));
                println!("Version: {:?}", version);
            }
            Err(status) => {
                let status_code = status.code();
                span.set_attribute(KeyValue::new(
                    "garf.error",
                    status_code.description(),
                ));
            }
        };
        Ok(())
    }

    pub async fn info(&self) -> GarfResult {
        let cx = telemetry::create_span("garf-rust", "info");
        let mut client = self.connect_client().await?;
        let req = telemetry::create_propagated_request(&cx, ());
        let response = client.get_info(req).await;
        let span = cx.span();
        let _ = match response {
            Ok(res) => {
                let info = &res.get_ref();
                span.set_attribute(KeyValue::new(
                    "garf.io.version",
                    info.io_version.clone(),
                ));
                span.set_attribute(KeyValue::new(
                    "garf.core.version",
                    info.core_version.clone(),
                ));
                span.set_attribute(KeyValue::new(
                    "garf.executors.version",
                    info.executors_version.clone(),
                ));
                println!("Info: {:?}", info);
            }
            Err(status) => {
                let status_code = status.code();
                span.set_attribute(KeyValue::new(
                    "garf.error",
                    status_code.description(),
                ));
            }
        };
        Ok(())
    }

    pub async fn fetchers(&self) -> GarfResult {
        let cx = telemetry::create_span("garf-rust", "list-fetchers");
        let mut client = self.connect_client().await?;
        let req = telemetry::create_propagated_request(&cx, ());
        let response = client.list_fetchers(req).await;
        let span = cx.span();
        let _ = match response {
            Ok(res) => {
                let fetchers = &res.get_ref().results;
                if let Ok(fetcher_str) = serde_json::to_string(&fetchers) {
                    span.set_attribute(KeyValue::new(
                        "garf.fetchers",
                        fetcher_str,
                    ));
                }
                println!("Fetchers: {:?}", &fetchers);
            }
            Err(status) => {
                let status_code = status.code();
                span.set_attribute(KeyValue::new(
                    "garf.error",
                    status_code.description(),
                ));
            }
        };
        Ok(())
    }

    pub async fn executors(&self) -> GarfResult {
        let cx = telemetry::create_span("garf-rust", "list-fetchers");
        let mut client = self.connect_client().await?;
        let req = telemetry::create_propagated_request(&cx, ());
        let response = client.list_executors(req).await;
        let span = cx.span();
        let _ = match response {
            Ok(res) => {
                let executors = &res.get_ref().results;
                if let Ok(executor_str) = serde_json::to_string(&executors) {
                    span.set_attribute(KeyValue::new(
                        "garf.executors",
                        executor_str,
                    ));
                }
                println!("Executors: {:?}", &executors);
            }
            Err(status) => {
                let status_code = status.code();
                span.set_attribute(KeyValue::new(
                    "garf.error",
                    status_code.description(),
                ));
            }
        };
        Ok(())
    }

    pub async fn execute(
        &self,
        query: &'static str,
        title: &'static str,
    ) -> GarfResult {
        let cx = telemetry::create_span("garf-rust", "execute");
        let mut client = self.connect_client().await?;
        let mut fields = BTreeMap::new();
        fields.insert(
            "n_rows".to_string(),
            Value {
                kind: Some(Kind::NumberValue(10f64)),
            },
        );
        let payload = garf::ExecuteRequest {
            source: "fake".to_string(),
            query: query.to_string(),
            title: title.to_string(),
            simulate: false,
            context: Some(garf::ExecutionContext {
                writers: vec!["json".to_string()],
                fetcher_parameters: Some(Struct { fields }),
                ..Default::default()
            }),
            ..Default::default()
        };
        let req = telemetry::create_propagated_request(&cx, payload.clone());
        let response = client.execute(req).await;
        let span = cx.span();
        let _ = match response {
            Ok(res) => {
                let results = &res.get_ref().results;
                span.set_attribute(KeyValue::new(
                    "garf.results",
                    results.join(","),
                ));
                println!("Query results: {:?}", results);
            }
            Err(status) => {
                let status_code = status.code();
                span.set_attribute(KeyValue::new(
                    "garf.error",
                    status_code.description(),
                ));
            }
        };
        Ok(())
    }

    pub async fn execute_batch(
        &self,
        batch: HashMap<&str, &str>,
    ) -> GarfResult {
        let cx = telemetry::create_span("garf-rust", "execute-batch");
        let mut client = self.connect_client().await?;
        let mut fields = BTreeMap::new();
        fields.insert(
            "n_rows".to_string(),
            Value {
                kind: Some(Kind::NumberValue(10f64)),
            },
        );
        let mut queries: Vec<garf::QueryDefinition> = vec![];
        for (k, v) in batch {
            queries.push(garf::QueryDefinition {
                title: k.to_string(),
                text: v.to_string(),
            });
        }
        let payload = garf::ExecuteBatchRequest {
            source: "fake".to_string(),
            batch: queries,
            simulate: false,
            context: Some(garf::ExecutionContext {
                writers: vec!["json".to_string()],
                fetcher_parameters: Some(Struct { fields }),
                ..Default::default()
            }),
            ..Default::default()
        };
        let req = telemetry::create_propagated_request(&cx, payload.clone());
        let response = client.execute_batch(req).await;
        let span = cx.span();
        let _ = match response {
            Ok(res) => {
                let results = &res.get_ref().results;
                span.set_attribute(KeyValue::new(
                    "garf.results",
                    results.join(","),
                ));
                println!("Batch results: {:?}", results);
            }
            Err(status) => {
                let status_code = status.code();
                span.set_attribute(KeyValue::new(
                    "garf.error",
                    status_code.description(),
                ));
            }
        };
        Ok(())
    }

    pub async fn execute_workflow(
        &self,
        workflow: Workflow,
        config: Config,
        execution_context: ExecutionContext,
    ) -> GarfResult {
        let cx = telemetry::create_span("garf-rust", "execute-workflow");
        let mut client = self.connect_client().await?;
        let mut fields = BTreeMap::new();
        fields.insert(
            "n_rows".to_string(),
            Value {
                kind: Some(Kind::NumberValue(10f64)),
            },
        );
        let payload = garf::ExecuteWorkflowRequest {
            workflow: Some(workflow),
            config: Some(config),
            context: Some(execution_context),
            ..Default::default()
        };
        let req = telemetry::create_propagated_request(&cx, payload.clone());
        let response = client.execute_workflow(req).await;
        let span = cx.span();
        let _ = match response {
            Ok(res) => {
                let results = &res.get_ref().results;
                span.set_attribute(KeyValue::new(
                    "garf.results",
                    results.join(","),
                ));
                println!("Workflow results: {:?}", results);
            }
            Err(status) => {
                let status_code = status.code();
                span.set_attribute(KeyValue::new(
                    "garf.error",
                    status_code.description(),
                ));
            }
        };
        Ok(())
    }
}
