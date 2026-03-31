# demo_app

Minimal C++17 demo project for CI log parsing experiments.

## Build

```bash
mkdir build
cd build
cmake ..
cmake --build .
```

## Run

```bash
./demo_app
```

Expected output:

```
=== demo_app ===
add(3, 4) = 7
divide(10.0, 3.0) = 3.33333
[warn] divide: division by zero, returning 0.0
divide(5.0, 0.0) = 0
is_number_positive(42) = true
is_number_positive(-1) = false
=== done ===
```
