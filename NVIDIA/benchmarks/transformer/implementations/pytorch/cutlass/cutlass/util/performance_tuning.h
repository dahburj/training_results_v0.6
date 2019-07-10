/******************************************************************************
 * Copyright (c) 2011-2017, NVIDIA CORPORATION.  All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are not permitted.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
 * ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
 * WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
 * DISCLAIMED. IN NO EVENT SHALL NVIDIA CORPORATION BE LIABLE FOR ANY
 * DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
 * (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
 * LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
 * ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
 * (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
 * SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 *
 ******************************************************************************/

#pragma once
#ifndef CUTLASS_PERFORMANCE_TUNING_H
#define CUTLASS_PERFORMANCE_TUNING_H

// CUTLASS_PRAGMA_(UNROLL|NO_UNROLL) optimization directives for the CUDA compiler.

#if defined(__CUDA_ARCH__)
#if defined(_MSC_VER)
#define CUTLASS_PRAGMA_UNROLL __pragma("unroll")
#define CUTLASS_PRAGMA_NO_UNROLL __pragma("unroll 1")
#else
#define CUTLASS_PRAGMA_UNROLL _Pragma("unroll")
#define CUTLASS_PRAGMA_NO_UNROLL _Pragma("unroll 1")
#endif
#else
#define CUTLASS_PRAGMA_UNROLL
#define CUTLASS_PRAGMA_NO_UNROLL
#endif

#define CUTLASS_GEMM_LOOP CUTLASS_PRAGMA_NO_UNROLL
#endif // CUTLASS_PERFORMANCE_TUNING_H