#!/usr/bin/env python3
"""
OpenCL Kernel Compilation Tester
--------------------------------
This script reads the OpenCL kernel from 'hashcat_rules_kernel.cl', compiles it
using PyOpenCL, and reports any compilation errors or success.

Usage:
    python test_kernel_compile.py [kernel_file]

If no kernel file is specified, it defaults to 'hashcat_rules_kernel.cl' in the
current directory.
"""

import sys
import os
import pyopencl as cl

def main():
    # Determine kernel file path
    if len(sys.argv) > 1:
        kernel_path = sys.argv[1]
    else:
        kernel_path = "hashcat_rules_kernel.cl"

    # Check if file exists
    if not os.path.isfile(kernel_path):
        print(f"Error: Kernel file '{kernel_path}' not found.")
        sys.exit(1)

    # Read kernel source
    with open(kernel_path, 'r') as f:
        kernel_source = f.read()

    print(f"Kernel source loaded from '{kernel_path}' ({len(kernel_source)} bytes).")

    # Initialize OpenCL context
    try:
        platforms = cl.get_platforms()
        if not platforms:
            print("No OpenCL platforms found.")
            sys.exit(1)

        # Use first platform and first device (GPU if available, otherwise CPU)
        platform = platforms[0]
        devices = platform.get_devices(cl.device_type.GPU)
        if not devices:
            devices = platform.get_devices(cl.device_type.CPU)
            if not devices:
                print("No OpenCL devices found.")
                sys.exit(1)

        device = devices[0]
        print(f"Using platform: {platform.name}")
        print(f"Using device: {device.name}")

        context = cl.Context([device])
        # Build program
        program = cl.Program(context, kernel_source)
        program.build()

        print("\nKernel compiled successfully!")

    except cl.RuntimeError as e:
        print("\nKernel compilation failed!")
        print("Error:", e)
        # Try to get build log
        try:
            build_log = program.get_build_info(device, cl.program_build_info.LOG)
            print("\nBuild log:")
            print(build_log)
        except:
            print("Could not retrieve build log.")
        sys.exit(1)

    except Exception as e:
        print("Unexpected error:", e)
        sys.exit(1)

if __name__ == "__main__":
    main()
