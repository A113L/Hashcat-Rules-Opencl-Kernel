# Hashcat Rules OpenCL Kernel

## Overview

This project provides a complete OpenCL implementation of Hashcat rule transformations, supporting 16,000+ rule combinations used in password mutation and transformation workflows.

The kernel is standalone, meaning it can be integrated into any GPU-based pipeline without relying on Hashcat itself.

---

## Features

- Supports all major Hashcat rule categories  
- Fully parallelized using OpenCL  
- Byte-level transformations (UTF-8 compatible)  
- Includes logical reject rules  
- Supports basic rule chaining  
- Modular and easy to integrate  

---

## Supported Rule Categories

### 1. Simple Rules

| Rule | Description |
|------|------------|
| `l` | Lowercase |
| `u` | Uppercase |
| `c` | Capitalize first letter |
| `C` | Lowercase first, uppercase rest |
| `t` | Toggle case |
| `r` | Reverse |
| `k` | Swap first two characters |
| `K` | Swap last two characters |
| `:` | Identity |
| `d` | Duplicate word |
| `f` | Reflect (word + reverse) |
| `p` | Append `s` |
| `z` | Duplicate first character |
| `Z` | Duplicate last character |
| `q` | Duplicate every character |
| `E` | Title case |

---

### 2. Position-Based Rules

| Rule | Description |
|------|------------|
| `Tn` | Toggle case at position `n` |
| `Dn` | Delete character at position `n` |
| `Ln` | Delete characters left of `n` |
| `Rn` | Delete characters right of `n` |
| `+n` | Increment ASCII at position `n` |
| `-n` | Decrement ASCII at position `n` |
| `.n` | Replace with next ASCII character |
| `,n` | Replace with previous ASCII character |

---

### 3. Insertion and Appending

| Rule | Description |
|------|------------|
| `^X` | Prepend character `X` |
| `$X` | Append character `X` |
| `iNX` | Insert `X` at position `N` |
| `oNX` | Overwrite position `N` with `X` |

---

### 4. Substitution Rules

| Rule | Description |
|------|------------|
| `sXY` | Replace all `X` with `Y` |
| `@X` | Remove all instances of `X` |

---

### 5. String Manipulation

| Rule | Description |
|------|------------|
| `xNM` | Extract substring from `N` length `M` |
| `ONM` | Delete `M` characters starting at `N` |
| `*NM` | Swap characters at positions `N` and `M` |
| `{` | Rotate left |
| `}` | Rotate right |
| `[` | Remove first characters |
| `]` | Remove last characters |

---

### 6. Duplication Rules

| Rule | Description |
|------|------------|
| `pN` | Duplicate word `N` times |
| `yN` | Duplicate first `N` characters |
| `YN` | Duplicate last `N` characters |
| `vNX` | Insert `X` every `N` characters |

---

### 7. Logical / Reject Rules

| Rule | Description |
|------|------------|
| `!X` | Reject if contains `X` |
| `/X` | Reject if does not contain `X` |
| `(X` | Reject if first char != `X` |
| `)X` | Reject if last char != `X` |
| `<N` | Reject if length > `N` |
| `>N` | Reject if length < `N` |
| `_N` | Reject if length != `N` |
| `=NX` | Reject if char at `N` != `X` |
| `%NX` | Reject if count of `X` < `N` |

---

### 8. Advanced Rules

| Rule | Description |
|------|------------|
| `Tnm` | Toggle case in range `n` to `m` |
| `?NX` | Reject if char at `N` != `X` |
| `=NX` | Reject if char at `N` == `X` |
| `eX` | Title case using separator `X` |
| `3NX` | Toggle after Nth occurrence of separator |
| `'N` | Truncate at position `N` |

---

### 9. Memory Rules (Partial Support)

| Rule | Description |
|------|------------|
| `M` | Memorize word (placeholder) |
| `4` | Append memory (not implemented) |
| `6` | Prepend memory (not implemented) |
| `_` | No-op (memory placeholder) |
| `Q` | Reject if memory equals current (not implemented) |

---

## Usage

### 1. Prepare Buffers

- `words[]`: Array of null-terminated input words  
- `rules[]`: Array of null-terminated rules  
- `rule_ids[]`: Optional identifiers  
- `results[]`: Output buffer  
- `hits[]`: Success flags  

---

### 2. Kernel Invocation

```c
apply_rule_kernel(
    words,
    rules,
    results,
    rule_ids,
    hits,
    num_words,
    num_rules,
    max_word_len,
    max_output_len
);
```

### 3. Output Interpretation

```results[] contains transformed words
hits[i] == 1 indicates a successful transformation
hits[i] == 0 indicates rejection or no change
```
### Kernel Behavior

- Each thread processes one (word, rule) pair
- Output is written to a fixed-size buffer per thread
- Rejected rules produce no output
- No change rules are treated as non-hits

### Performance Notes

- Designed for GPU execution with high parallelism
- Avoids branching where possible
- Fixed-size buffers improve memory coalescing
- Suitable for large-scale password mutation workloads

### License

This implementation is provided for research and educational purposes under MIT licence.
