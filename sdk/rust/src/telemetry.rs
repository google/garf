use anyhow::Result;
use opentelemetry::{
    Context, global,
    propagation::Injector,
    trace::{SpanKind, TraceContextExt, Tracer},
};
use opentelemetry_otlp::{LogExporter, MetricExporter, SpanExporter};
use opentelemetry_sdk::logs::SdkLoggerProvider;
use opentelemetry_sdk::metrics::SdkMeterProvider;
use opentelemetry_sdk::trace::SdkTracerProvider;
use opentelemetry_sdk::{Resource, propagation::TraceContextPropagator};

struct MetadataMap<'a>(&'a mut tonic::metadata::MetadataMap);

impl Injector for MetadataMap<'_> {
    /// Set a key and value in the MetadataMap.  Does nothing if the key or value are not valid inputs
    fn set(&mut self, key: &str, value: String) {
        if let Ok(key) = tonic::metadata::MetadataKey::from_bytes(key.as_bytes()) {
            if let Ok(val) = tonic::metadata::MetadataValue::try_from(&value) {
                self.0.insert(key, val);
            }
        }
    }
}

pub struct OtelGuard {
    tracer_provider: SdkTracerProvider,
    meter_provider: SdkMeterProvider,
    logger_provider: SdkLoggerProvider,
}

impl OtelGuard {
    pub fn shutdown(self) {
        if let Err(err) = self.tracer_provider.shutdown() {
            eprintln!("Error shutting down tracer provider: {err:?}");
        }
        if let Err(err) = self.meter_provider.shutdown() {
            eprintln!("Error shutting down meter provider: {err:?}");
        }
        if let Err(err) = self.logger_provider.shutdown() {
            eprintln!("Error shutting down logger provider: {err:?}");
        }
    }
}

pub fn setup_otel() -> Result<OtelGuard> {
    let tracer_provider = init_tracer_provider();
    let meter_provider = init_meter_provider();
    let logger_provider = init_logger_provider();
    Ok(OtelGuard {
        tracer_provider,
        meter_provider,
        logger_provider,
    })
}

pub fn init_tracer_provider() -> SdkTracerProvider {
    let exporter = SpanExporter::builder()
        .with_tonic()
        .build()
        .expect("Failed to create span exporter");

    let provider = SdkTracerProvider::builder()
        .with_resource(Resource::builder().with_service_name("garf-rust").build())
        .with_batch_exporter(exporter)
        .build();
    global::set_text_map_propagator(TraceContextPropagator::new());
    global::set_tracer_provider(provider.clone());
    provider
}

pub fn init_meter_provider() -> SdkMeterProvider {
    let exporter = MetricExporter::builder()
        .with_http()
        .build()
        .expect("Failed to initialize metric exporter");

    let provider = SdkMeterProvider::builder()
        .with_resource(Resource::builder().with_service_name("garf-rust").build())
        .with_periodic_exporter(exporter)
        .build();
    global::set_meter_provider(provider.clone());
    provider
}

pub fn init_logger_provider() -> SdkLoggerProvider {
    let exporter = LogExporter::builder()
        .with_http()
        .build()
        .expect("Failed to initialize logger");

    SdkLoggerProvider::builder()
        .with_resource(Resource::builder().with_service_name("garf-rust").build())
        .with_batch_exporter(exporter)
        .build()
}

pub fn create_span(tracer: &'static str, span: &'static str) -> Context {
    let tracer = global::tracer(tracer);
    let span = tracer
        .span_builder(span)
        .with_kind(SpanKind::Client)
        .start(&tracer);
    Context::current_with_span(span)
}

pub fn create_propagated_request<T>(cx: &Context, message: T) -> tonic::Request<T> {
    let mut req = tonic::Request::new(message);
    global::get_text_map_propagator(|propagator| {
        propagator.inject_context(&cx, &mut MetadataMap(req.metadata_mut()))
    });
    req
}
