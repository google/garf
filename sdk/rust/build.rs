use std::io::Result;

fn main() -> Result<()> {
    let mut config = tonic_prost_build::configure();
    let serializable_types = [".garf.FetcherInfo"];

    for proto_type in serializable_types {
        config =
            config.type_attribute(proto_type, "#[derive(serde::Serialize)]")
    }
    config
        .build_server(false) // .out_dir("src")
        .compile_protos(
            &["../../protos/garf.proto"],
            &["../../protos", "src"],
        )?;
    Ok(())
}
