# AgateDB

[![Coverage Status](https://codecov.io/gh/tikv/agatedb/branch/master/graph/badge.svg)](https://codecov.io/gh/tikv/agatedb)

AgateDB is an embeddable, persistent and fast key-value (KV) database written
in pure Rust. It is designed as an experimental engine for the [TiKV][1]
project, and will bring aggressive optimizations for TiKV specifically.

## Features

- **Embeddable**: Designed to be embedded directly into your Rust applications
- **Persistent**: Data is persisted to disk with durability guarantees
- **MVCC Support**: Multi-version concurrency control for transactional operations
- **High Performance**: Optimized for speed and efficiency
- **Memory Safe**: Written in Rust, providing memory safety guarantees
- **Badger Compatible**: Implements most functionalities of Badger managed mode

## Project Status

AgateDB is still under early heavy development. You can check the development
progress at the [GitHub Project][2].

The whole plan is to port [Badger][3] in Rust first and then port the
optimizations that have been made in [Unistore][4].

AgateDB is under active development on the [develop](https://github.com/tikv/agatedb/tree/develop)
branch. Currently, it can be used as a key-value store with MVCC. It implements most of the
functionalities of Badger managed mode.

## Installation

Add AgateDB to your `Cargo.toml`:

```toml
[dependencies]
agatedb = { git = "https://github.com/tikv/agatedb" }
```

Or if you need RocksDB benchmarking support:

```toml
[dependencies]
agatedb = { git = "https://github.com/tikv/agatedb", features = ["enable-rocksdb"] }
```

## Usage

Here's a simple example of how to use AgateDB:

```rust
use agatedb::AgateOptions;
use bytes::Bytes;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Create options
    let mut opts = AgateOptions::default();
    opts.dir = std::path::PathBuf::from("./data");
    opts.value_dir = opts.dir.clone();
    opts.managed_txns = true; // Enable managed transactions
    
    // Open database
    let db = opts.open()?;
    
    // Write data using a transaction
    let mut txn = db.new_transaction_at(1, true);
    let key = Bytes::from("hello");
    let value = Bytes::from("world");
    txn.set(key.clone(), value)?;
    txn.commit_at(1)?;
    
    // Read data using a transaction
    let mut txn = db.new_transaction_at(1, false);
    match txn.get(&key) {
        Ok(item) => println!("Value: {:?}", item.vptr),
        Err(_) => println!("Key not found"),
    }
    txn.discard();
    
    // Database is automatically closed when dropped
    Ok(())
}
```

For more advanced usage, including batch operations and iterators, please refer to the [documentation](https://docs.rs/agatedb) and test files.

## Building

To build AgateDB:

```bash
cargo build --release
```

To run tests:

```bash
cargo test
```

To run benchmarks:

```bash
cargo bench
```

## Why AgateDB?

The motivation of this project is to ultimately land the
optimizations we have been made to Unistore in TiKV. Unistore is based
on Badger, so we start with Badger.

We are using Rust because it can bring memory safety out of box, which is important
during rapid development. TiKV is also written in Rust, so it will be easier
to integrate with each other like supporting async/await, sharing global
thread pools, etc.

## Benchmarks

We continuously benchmark AgateDB against RocksDB. You can refer to 
[this page](https://tikv.github.io/agatedb/dev/bench/) for the benchmark results.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

Licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE) for details.

## Links

- [TiKV][1] - Distributed transactional key-value database
- [GitHub Project][2] - Development progress tracking
- [Badger][3] - Original Badger implementation
- [Unistore][4] - Optimized Badger implementation

[1]: https://github.com/tikv/tikv
[2]: https://github.com/tikv/agatedb/projects/1
[3]: https://github.com/outcaste-io/badger/tree/45bca18f24ef5cc04701a1e17448ddfce9372da0
[4]: https://github.com/ngaut/unistore
