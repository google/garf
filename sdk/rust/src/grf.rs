pub mod garf {
    tonic::include_proto!("garf");
}
use crate::telemetry;
use garf::garf_service_client::GarfServiceClient;
use opentelemetry::{KeyValue, trace::TraceContextExt};
use prost_types::{Struct, Value, value::Kind};
use std::collections::BTreeMap;

type GarfResult = Result<(), Box<dyn std::error::Error + Send + Sync + 'static>>;

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
    ) -> Result<GarfServiceClient<tonic::transport::Channel>, tonic::transport::Error> {
        GarfServiceClient::connect(self.endpoint.clone()).await
    }

    pub async fn version(&self) -> GarfResult {
        let cx = telemetry::create_span("garf-rust", "version");
        let mut client = self.connect_client().await?;
        let req = telemetry::create_propagated_request(&cx, ());
        let response = client.get_version(req).await;
        let span = cx.span();
        let status = match response {
            Ok(_res) => {
                span.set_attribute(KeyValue::new("version", "0"));
            }
            Err(status) => {
                let status_code = status.code();
                span.set_attribute(KeyValue::new("fetcher", status_code.description()));
            }
        };
        println!("Version: {:?}", status);
        Ok(())
    }

    pub async fn fetchers(&self) -> GarfResult {
        let cx = telemetry::create_span("garf-rust", "fetchers");
        let mut client = self.connect_client().await?;
        let req = telemetry::create_propagated_request(&cx, ());
        let response = client.list_fetchers(req).await;
        let span = cx.span();
        let status = match response {
            Ok(_res) => {
                span.set_attribute(KeyValue::new("version", "0"));
            }
            Err(status) => {
                let status_code = status.code();
                span.set_attribute(KeyValue::new("fetcher", status_code.description()));
            }
        };
        println!("Version: {:?}", status);
        Ok(())
    }

    pub async fn execute(&self, query: &'static str, title: &'static str) -> GarfResult {
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
        let status = match response {
            Ok(_res) => {
                span.set_attribute(KeyValue::new("version", "0"));
            }
            Err(status) => {
                let status_code = status.code();
                span.set_attribute(KeyValue::new("fetcher", status_code.description()));
            }
        };
        println!("Version: {:?}", status);
        Ok(())
    }
}
