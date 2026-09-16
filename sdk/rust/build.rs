use std::io::Result;

fn main() -> Result<()> {
    tonic_prost_build::configure()
        .build_server(false)
        // .out_dir("src")
        .type_attribute(".", "#[derive(serde::Serialize, serde::Deserialize)]")
        .field_attribute(".", "#[serde(default)]")
        .extern_path(".google.protobuf.Struct", "::pbjson_types::Struct")
        .extern_path(".google.protobuf.Value", "::pbjson_types::Value")
        .compile_protos(
            &["../../protos/garf.proto"],
            &["../../protos", "src"],
        )?;
    Ok(())
}
