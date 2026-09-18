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
use anyhow::Result;
use clap::{Parser, Subcommand};
use garf::{self, Garf};
use std::{env, fs};

#[derive(Parser, Debug)]
#[command(name = "garf", version = "0.0.1")]
struct Cli {
    #[arg(
        long,
        env = "GARF_ENDPOINT",
        default_value = "http://127.0.0.1:50051",
        global = true
    )]
    endpoint: String,

    #[arg(long, action = clap::ArgAction::SetTrue, global=true)]
    enable_cache: bool,

    #[command(subcommand)]
    command: Option<Commands>,
}
#[derive(Subcommand, Debug)]
enum Server {
    Version,
    Info,
    Fetchers,
    Executors,
}
#[derive(Subcommand, Debug)]
enum Workflow {
    Run {
        #[arg(short, long)]
        file: String,
        #[arg(short, long)]
        config: Option<String>,
    },
}

#[derive(Subcommand, Debug)]
enum Commands {
    #[command(subcommand)]
    Server(Server),
    Execute {
        query: String,
    },
    #[command(subcommand)]
    Workflow(Workflow),
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error + Send + Sync + 'static>>
{
    let mut otel_guard = None;
    if env::var("OTEL_EXPORTER_OTLP_ENDPOINT").is_ok() {
        match garf::telemetry::setup_otel() {
            Ok(guard) => otel_guard = Some(guard),
            Err(err) => {
                panic!("Couldn't start Otel: {0}", err);
            }
        }
    }
    let _ = garf::telemetry::create_span("garf-rust", "run");
    let cli = Cli::parse();
    let g = Garf::new(&cli.endpoint);
    match cli.command {
        Some(Commands::Server(Server::Version)) => {
            g.version().await?;
        }
        Some(Commands::Server(Server::Info)) => {
            g.info().await?;
        }
        Some(Commands::Server(Server::Fetchers)) => {
            g.fetchers().await?;
        }
        Some(Commands::Server(Server::Executors)) => {
            g.executors().await?;
        }
        Some(Commands::Execute { query }) => {
            let query_text = fs::read_to_string(query.clone()).unwrap();
            let path = std::path::PathBuf::from(&query);
            let title: &str = match path.file_stem() {
                Some(os_str) => match os_str.to_str() {
                    Some(s) => s,
                    None => "unknown",
                },
                None => "unknown",
            };
            g.execute(&query_text, title).await?;
        }
        Some(Commands::Workflow(Workflow::Run { file, config })) => {
            let workflow: garf::garf::Workflow =
                garf::read_from_file(file.clone().into())?;
            if let Some(_config) = config {
                let _config: garf::garf::Config =
                    garf::read_from_file(_config.clone().into())?;
            }
            g.execute_workflow(
                workflow,
                garf::garf::Config::default(),
                garf::garf::ExecutionContext::default(),
            )
            .await?;
        }
        _ => {
            eprintln!("Unknown command");
        }
    }
    if let Some(guard) = otel_guard {
        guard.shutdown();
    }
    Ok(())
}
