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

pub mod garf {
    tonic::include_proto!("garf");
}
pub mod telemetry;
use anyhow::Result;
use garf::garf_service_client::GarfServiceClient;
use garf::{Config, ExecutionContext, Workflow};
use opentelemetry::{KeyValue, trace::TraceContextExt};
use pbjson_types::{Struct, Value, value::Kind};
use serde;
use serde_json;
use serde_yaml_bw;
use std::collections::HashMap;
use std::error::Error;
use std::fs::File;
use tabled;

type GarfResult = Result<(), Box<dyn Error + Send + Sync + 'static>>;

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
                println!("Info: {:#?}", info);
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
                println!("Fetchers: {:#?}", &fetchers);
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

    pub async fn fetch(
        &self,
        query: impl Into<String>,
        title: impl Into<String>,
    ) -> GarfResult {
        let cx = telemetry::create_span("garf-rust", "fetch");
        let mut client = self.connect_client().await?;
        let mut fields = HashMap::new();
        fields.insert(
            "n_rows".to_string(),
            Value {
                kind: Some(Kind::NumberValue(10f64)),
            },
        );
        let payload = garf::FetchRequest {
            source: "fake".to_string(),
            query: query.into(),
            title: title.into(),
            simulate: false,
            context: Some(garf::FetchContext {
                fetcher_parameters: Some(Struct { fields }),
                ..Default::default()
            }),
            ..Default::default()
        };
        let req = telemetry::create_propagated_request(&cx, payload.clone());
        let response = client.fetch(req).await;
        let span = cx.span();
        let _ = match response {
            Ok(res) => {
                let results = &res.get_ref();
                let headers = results.columns.clone();
                let mut builder = tabled::builder::Builder::new();
                builder.push_record(headers);
                for row in &results.rows {
                    let mut row_strings: Vec<String> = Vec::new();
                    let fields = &row.fields;
                    for col in &results.columns {
                        let cell_value = match fields.get(col) {
                            Some(Value { kind: Some(kind) }) => match kind {
                                Kind::NullValue(_) => "".to_string(),
                                Kind::NumberValue(n) => n.to_string(),
                                Kind::StringValue(s) => s.clone(),
                                Kind::BoolValue(b) => b.to_string(),
                                Kind::StructValue(_) => "[Object]".to_string(),
                                Kind::ListValue(_) => "[Array]".to_string(),
                            },
                            _ => "".to_string(),
                        };
                        row_strings.push(cell_value);
                    }
                    builder.push_record(row_strings);
                }
                let table = builder.build();
                println!("Fetch results:\n {}", table);
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
        query: impl Into<String>,
        title: impl Into<String>,
    ) -> GarfResult {
        let cx = telemetry::create_span("garf-rust", "execute");
        let mut client = self.connect_client().await?;
        let mut fields = HashMap::new();
        fields.insert(
            "n_rows".to_string(),
            Value {
                kind: Some(Kind::NumberValue(10f64)),
            },
        );
        let payload = garf::ExecuteRequest {
            source: "fake".to_string(),
            query: query.into(),
            title: title.into(),
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
        let mut fields = HashMap::new();
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

pub fn read_from_file<T: serde::de::DeserializeOwned>(
    file: std::borrow::Cow<'static, str>,
) -> Result<T> {
    let file_path = File::open(file.as_ref())?;
    let yaml_data: serde_yaml_bw::Value =
        serde_yaml_bw::from_reader(file_path)?;
    let json_value: serde_json::Value = serde_json::to_value(yaml_data)?;

    let data: T = serde_json::from_value(json_value)?;
    Ok(data)
}
