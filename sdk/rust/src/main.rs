mod grf;
mod telemetry;
use grf::Garf;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error + Send + Sync + 'static>> {
    let otel_guard = match telemetry::setup_otel() {
        Ok(guard) => guard,
        Err(err) => {
            panic!("Couldn't start Otel: {0}", err);
        }
    };
    let _ = telemetry::create_span("garf-rust", "run");
    let g = Garf::new("http://127.0.0.1:50051");

    g.version().await?;
    g.fetchers().await?;
    g.execute("SELECT metric.int AS field FROM fake", "test")
        .await?;
    otel_guard.shutdown();
    Ok(())
}
