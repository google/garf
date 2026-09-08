use std::io::Result;

fn main() -> Result<()> {
    tonic_prost_build::configure()
        .build_server(false)
        // .out_dir("src")
        .compile_protos(&["../../protos/garf.proto"], &["../../protos", "src"])?;
    Ok(())
}
