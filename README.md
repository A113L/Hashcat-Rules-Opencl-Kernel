# hashcat_rules_kernel.cl

An OpenCL kernel implementing the complete Hashcat rule engine for GPU-accelerated password candidate generation. Supports all major rule transformations including case manipulation, character substitution, insertion, deletion, rotation, and logical rejection rules.

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Rule Reference](#rule-reference)
  - [Simple Rules](#simple-rules)
  - [Position-Based Rules](#position-based-rules)
  - [Three-Character Rules](#three-character-rules)
  - [Reject Rules](#reject-rules)
  - [Memory Operations](#memory-operations)
- [API Reference](#api-reference)
  - [apply_rule_kernel](#apply_rule_kernel)
  - [apply_rule_chain_kernel](#apply_rule_chain_kernel)
  - [Utility Functions](#utility-functions)
- [Usage](#usage)
- [Constants](#constants)
- [Limitations](#limitations)
- [Compatibility](#compatibility)

---

## Overview

This kernel processes word/rule pairs in parallel across GPU threads. Each thread applies one rule to one input word and writes the result to a pre-allocated output buffer, flagging hits for downstream collection.

```
words[] × rules[]  →  [kernel]  →  results[] + hits[]
```

Rules are encoded as short null-terminated strings (up to 16 bytes). The kernel dispatches on `rule_len` (1, 2, or 3 characters) and branches on the leading command byte.

---

## Features

- ✅ All simple single-character transformations (`l`, `u`, `c`, `t`, `r`, `d`, `f`, `q`, `E`, …)
- ✅ Position-based operations (`T`, `D`, `L`, `R`, `+`, `-`, `^`, `$`, `@`, `p`, `y`, `Y`, `'`)
- ✅ Three-character compound rules (`sXY`, `*NM`, `xNM`, `ONM`, `iNX`, `oNX`, `eX`, `3NX`, `vNX`)
- ✅ Logical reject rules (`!X`, `/X`, `(X`, `)X`, `<N`, `>N`, `_N`, `=NX`, `?NX`, `%NX`)
- ✅ Thread-safe parallel execution across word/rule pairs
- ✅ UTF-8 byte-level compatible
- ⚠️ Memory operations (`M`, `4`, `6`) stubbed — no cross-thread state

---

## Rule Reference

Position arguments use Hashcat's extended base-36 encoding: `0`–`9` map to 0–9, `A`–`Z` map to 10–35.

### Simple Rules

| Rule | Description | Example |
|------|-------------|---------|
| `:` | No-op / identity | `password` → `password` |
| `l` | Lowercase all | `PaSsWoRd` → `password` |
| `u` | Uppercase all | `password` → `PASSWORD` |
| `c` | Capitalize first, lowercase rest | `pASSWORD` → `Password` |
| `C` | Lowercase first, uppercase rest | `Password` → `pASSWORD` |
| `t` | Toggle case of every character | `Password` → `pASSWORD` |
| `r` | Reverse | `password` → `drowssap` |
| `d` | Duplicate whole word | `pass` → `passpass` |
| `f` | Reflect (word + reversed word) | `pass` → `passsap` |
| `k` | Swap first two characters | `password` → `apssword` |
| `K` | Swap last two characters | `password` → `passwrod` |
| `q` | Duplicate every character | `pas` → `ppaass` |
| `z` | Prepend first character | `pass` → `ppass` |
| `Z` | Append last character | `pass` → `passs` |
| `p` | Append `s` (pluralize) | `pass` → `passs` |
| `E` | Title-case on space/`-`/`_` | `hello world` → `Hello World` |
| `[` | Delete first character | `password` → `assword` |
| `]` | Delete last character | `password` → `passwor` |
| `{` | Rotate left (first char moves to end) | `password` → `asswordp` |
| `}` | Rotate right (last char moves to front) | `password` → `dpasswor` |

---

### Position-Based Rules

`N` / `M` are base-36 position arguments.

| Rule | Description |
|------|-------------|
| `TN` | Toggle case at position N |
| `DN` | Delete character at position N |
| `LN` | Delete all characters left of position N |
| `RN` | Delete all characters right of position N |
| `+N` | Increment ASCII value of character at N |
| `-N` | Decrement ASCII value of character at N |
| `.N` | Replace character at N with next ASCII character |
| `,N` | Replace character at N with previous ASCII character |
| `^X` | Prepend character X |
| `$X` | Append character X |
| `@X` | Remove all occurrences of character X |
| `pN` | Duplicate word N times |
| `yN` | Prepend first N characters to end |
| `YN` | Append last N characters to end |
| `'N` | Truncate to first N characters |

---

### Three-Character Rules

| Rule | Description |
|------|-------------|
| `sXY` | Substitute all X → Y |
| `*NM` | Swap characters at positions N and M |
| `xNM` | Extract substring from position N of length M |
| `ONM` | Omit M characters starting at position N |
| `iNX` | Insert character X at position N |
| `oNX` | Overwrite character at position N with X |
| `eX` | Title-case using X as word separator |
| `3NX` | Toggle case of character after the Nth occurrence of separator X |
| `vNX` | Insert X after every N characters |

---

### Reject Rules

Reject rules cause the word/rule pair to produce no output (`hits[gid] = 0`).

| Rule | Rejects when… |
|------|---------------|
| `!X` | Word **contains** character X |
| `/X` | Word does **not** contain character X |
| `(X` | First character is **not** X |
| `)X` | Last character is **not** X |
| `<N` | Word length **exceeds** N |
| `>N` | Word length is **less than** N |
| `_N` | Word length is **not equal** to N |
| `=NX` | Character at position N **equals** X (3-char form) |
| `?NX` | Character at position N is **not** X (3-char form) |
| `%NX` | Count of X in word is **less than** N |
| `Q` | Always reject (memory equality placeholder) |

---

### Memory Operations

These are stubbed. The word passes through unchanged; no global memory state is maintained.

| Rule | Description |
|------|-------------|
| `M` | Memorize current word |
| `4` | Append memorized string |
| `6` | Prepend memorized string |
| `_` | No-op placeholder |

---

## API Reference

### `apply_rule_kernel`

```c
__kernel void apply_rule_kernel(
    __global const unsigned char* words,       // Packed input words
    __global const unsigned char* rules,       // Packed rule strings
    __global unsigned char*       results,     // Packed output words
    __global int*                 rule_ids,    // Rule index per slot
    __global int*                 hits,        // 1 = match, 0 = reject/no-op
    const int num_words,
    const int num_rules,
    const int max_word_len,
    const int max_output_len
);
```

**Global work size:** `num_words × num_rules`

Each work item at global ID `gid` processes:
- Word index: `gid / num_rules`
- Rule index: `gid % num_rules`

**Outputs:**
- `results[gid * max_output_len]` — transformed word (null-terminated)
- `hits[gid]` — `1` if the rule produced output, `0` otherwise

---

### `apply_rule_chain_kernel`

```c
__kernel void apply_rule_chain_kernel(
    __global const unsigned char* words,
    __global const unsigned char* rules,
    __global const int*           rule_chain,
    __global unsigned char*       results,
    __global int*                 hits,
    const int num_words,
    const int num_rules_per_chain,
    const int chain_length,
    const int max_word_len,
    const int max_output_len
);
```

Chains multiple rules sequentially per word. Memory operations are not supported in chained mode. Provide the rule execution order via `rule_chain[]`.

---

### Utility Functions

These are device-side helpers used internally by the kernels.

| Function | Signature | Description |
|----------|-----------|-------------|
| `parse_position` | `int parse_position(unsigned char c)` | Decodes base-36 position argument |
| `count_char` | `int count_char(const unsigned char*, int, unsigned char)` | Counts occurrences of a byte |
| `is_lower` | `int is_lower(unsigned char c)` | True if `a`–`z` |
| `is_upper` | `int is_upper(unsigned char c)` | True if `A`–`Z` |
| `is_digit` | `int is_digit(unsigned char c)` | True if `0`–`9` |
| `is_alnum` | `int is_alnum(unsigned char c)` | True if alphanumeric |
| `toggle_case` | `unsigned char toggle_case(unsigned char c)` | Flips upper/lowercase |
| `to_lower` | `unsigned char to_lower(unsigned char c)` | Converts to lowercase |
| `to_upper` | `unsigned char to_upper(unsigned char c)` | Converts to uppercase |

---

## Usage

```c
// 1. Allocate and populate host buffers
unsigned char* h_words   = ...;  // num_words × max_word_len
unsigned char* h_rules   = ...;  // num_rules × MAX_RULE_LEN
int*           h_rule_ids = ...;
unsigned char* h_results = ...;  // num_words × num_rules × max_output_len
int*           h_hits    = ...;  // num_words × num_rules

// 2. Transfer to device
cl_mem d_words   = clCreateBuffer(ctx, CL_MEM_READ_ONLY  | CL_MEM_COPY_HOST_PTR, ...);
cl_mem d_rules   = clCreateBuffer(ctx, CL_MEM_READ_ONLY  | CL_MEM_COPY_HOST_PTR, ...);
cl_mem d_results = clCreateBuffer(ctx, CL_MEM_WRITE_ONLY, ...);
cl_mem d_hits    = clCreateBuffer(ctx, CL_MEM_WRITE_ONLY, ...);

// 3. Set kernel arguments and launch
clSetKernelArg(kernel, 0, sizeof(cl_mem), &d_words);
clSetKernelArg(kernel, 1, sizeof(cl_mem), &d_rules);
clSetKernelArg(kernel, 2, sizeof(cl_mem), &d_results);
clSetKernelArg(kernel, 3, sizeof(cl_mem), &d_rule_ids);
clSetKernelArg(kernel, 4, sizeof(cl_mem), &d_hits);
clSetKernelArg(kernel, 5, sizeof(int),    &num_words);
clSetKernelArg(kernel, 6, sizeof(int),    &num_rules);
clSetKernelArg(kernel, 7, sizeof(int),    &max_word_len);
clSetKernelArg(kernel, 8, sizeof(int),    &max_output_len);

size_t global_size = num_words * num_rules;
clEnqueueNDRangeKernel(queue, kernel, 1, NULL, &global_size, NULL, 0, NULL, NULL);

// 4. Read back results
clEnqueueReadBuffer(queue, d_results, CL_TRUE, 0, results_size, h_results, ...);
clEnqueueReadBuffer(queue, d_hits,    CL_TRUE, 0, hits_size,    h_hits,    ...);

// 5. Collect hits
for (int i = 0; i < num_words * num_rules; i++) {
    if (h_hits[i]) {
        // h_results[i * max_output_len] is a valid transformed candidate
    }
}
```

---

## Constants

| Constant | Value | Description |
|----------|-------|-------------|
| `MAX_WORD_LEN` | `256` | Maximum input word length (bytes) |
| `MAX_RULE_LEN` | `255` | Maximum rule string length (bytes) |
| `MAX_OUTPUT_LEN` | `512` | Maximum output word length (bytes) |

---

## Limitations

- **Memory operations** (`M`, `4`, `6`, `Q`) are not functional. Each work item is stateless; cross-thread state is not supported in the current architecture.
- **Rule chaining** in `apply_rule_chain_kernel` does not support memory operations.
- Rules longer than **3 characters** are not dispatched. Compound multi-rule sequences must be split and chained via `apply_rule_chain_kernel`.
- Output is truncated to `MAX_OUTPUT_LEN - 1` bytes.
- Non-ASCII bytes pass through unchanged; rules operate at the **byte level**, not Unicode code points.

---

## Compatibility

| Requirement | Details |
|-------------|---------|
| OpenCL version | 1.2+ |
| Tested on | NVIDIA (CUDA backend), AMD (ROCm), Intel OpenCL |
| Rule compatibility | Hashcat rule engine v6.x |
| Encoding | Byte-level; UTF-8 safe for non-transforming rules |

# OpenCL Kernel Compilation Tester

A minimal Python script that compiles an OpenCL kernel file and reports success or build errors.

## Requirements

```
pip install pyopencl
```

### An OpenCL-capable platform (GPU or CPU) must be available on the system.

## Usage

```bash
# Default — looks for hashcat_rules_kernel.cl in the current directory
python test_kernel_compile.py

# Specify a kernel file
python test_kernel_compile.py hashcat_rules_kernel.cl
```

## Output

On success:
```
Kernel source loaded from 'hashcat_rules_kernel.cl' (12345 bytes).
Using platform: NVIDIA CUDA
Using device: NVIDIA GeForce RTX 3080
Kernel compiled successfully!
```

On failure, the script prints the OpenCL build log and exits with code `1`.

## Notes

- Automatically selects the first available GPU, falling back to CPU if none is found.
- Does not execute the kernel — compilation only.


