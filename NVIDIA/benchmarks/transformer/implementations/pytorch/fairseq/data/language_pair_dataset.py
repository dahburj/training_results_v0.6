# Copyright (c) 2017-present, Facebook, Inc.
# All rights reserved.
#
# This source code is licensed under the license found in the LICENSE file in
# the root directory of this source tree. An additional grant of patent rights
# can be found in the PATENTS file in the same directory.

import numpy as np
import torch

from . import data_utils, FairseqDataset


def collate(samples, pad_idx, eos_idx, left_pad_source=True, left_pad_target=False, bsz_mult=8, seq_len_multiple=1):
    if len(samples) == 0:
        return {}

    def merge(key, left_pad, move_eos_to_beginning=False):
        return data_utils.collate_tokens(
            [s[key] for s in samples],
            pad_idx,
            eos_idx,
            left_pad,
            move_eos_to_beginning,
            bsz_mult,
            seq_len_multiple
        )

    id = torch.LongTensor([s['id'] for s in samples])
    src_tokens = merge('source', left_pad=left_pad_source)
    # sort by descending source length
    src_lengths = torch.LongTensor([s['source'].numel() for s in samples])

    prev_output_tokens = None
    target = None
    if samples[0].get('target', None) is not None:
        target = merge('target', left_pad=left_pad_target)
        # we create a shifted version of targets for feeding the
        # previous output token(s) into the next decoder step
        prev_output_tokens = merge(
            'target',
            left_pad=left_pad_target,
            move_eos_to_beginning=True,
        )
        ntokens = sum(len(s['target']) for s in samples)
    else:
        ntokens = sum(len(s['source']) for s in samples)

    return {
        'id': id,
        'ntokens': ntokens,
        'net_input': {
            'src_tokens': src_tokens,
            'src_lengths': src_lengths,
            'prev_output_tokens': prev_output_tokens,
        },
        'target': target,
    }


class LanguagePairDataset(FairseqDataset):
    """A pair of torch.utils.data.Datasets."""

    def __init__(
            self,
            src,
            src_sizes,
            src_dict,
            tgt=None,
            tgt_sizes=None,
            tgt_dict=None,
            left_pad_source=True,
            left_pad_target=False,
            max_source_positions=256,
            max_target_positions=256,
            seq_len_multiple=1,
            shuffle=True
    ):
        if tgt_dict is not None:
            assert src_dict.pad() == tgt_dict.pad()
            assert src_dict.eos() == tgt_dict.eos()

        self.src = src
        self.tgt = tgt

        self.src_sizes = np.array(src_sizes)
        self.tgt_sizes = np.array(tgt_sizes) if tgt_sizes is not None else None

        self.src_dict = src_dict
        self.tgt_dict = tgt_dict

        self.left_pad_source = left_pad_source
        self.left_pad_target = left_pad_target

        self.max_source_positions = max_source_positions
        self.max_target_positions = max_target_positions

        self.seq_len_multiple = seq_len_multiple

        self.shuffle = shuffle

        print("| Sentences are being padded to multiples of: {}".format(self.seq_len_multiple))


    def __getitem__(self, index):
        return {
            'id': index,
            'source': self.src[index],
            'target': self.tgt[index] if self.tgt is not None else None,
        }


    def __len__(self):
        return len(self.src)


    def collater(self, samples):
        """Merge a list of samples to form a mini-batch."""
        return collate(
            samples,
            pad_idx=self.src_dict.pad(),
            eos_idx=self.src_dict.eos(),
            left_pad_source=self.left_pad_source,
            left_pad_target=self.left_pad_target,
            bsz_mult=8,
            seq_len_multiple=self.seq_len_multiple,
        )


    def get_dummy_batch(self, max_tokens_per_batch, max_positions, src_len=256, tgt_len=256):
        max_source_positions, max_target_positions = self._get_max_positions(max_positions)
        src_len, tgt_len = min(src_len, max_source_positions), min(tgt_len, max_target_positions)
        n_seq_per_batch_based_on_longest_seq = max_tokens_per_batch // max(src_len, tgt_len)

        return self.collater([
            {
                'id': i,
                'source': self.src_dict.dummy_sentence(src_len),
                'target': self.tgt_dict.dummy_sentence(tgt_len) if self.tgt_dict is not None else None,
            }
            for i in range(n_seq_per_batch_based_on_longest_seq)
        ])


    def num_tokens(self, index):
        """Return an example's length (number of tokens), used for batching.

        Args:
            index: points to the sequence pair
        """
        n_tok_per_seq = max(self.src_sizes[index], self.tgt_sizes[index] if self.tgt_sizes is not None else 0)

        assert self.seq_len_multiple > 0, "Padding multiple has to be greater than 0"

        n_tok_per_seq = (n_tok_per_seq + self.seq_len_multiple - 1) // self.seq_len_multiple * self.seq_len_multiple  # Padded seq len, rounded up to next multiple

        return n_tok_per_seq


    def ordered_indices(self, seed=None, epoch=1):
        """Ordered indices for batching."""
        if self.shuffle:
            indices = np.random.RandomState(seed + epoch).permutation(len(self))
        else:
            indices = np.arange(len(self))

        if self.tgt_sizes is not None:
            indices = indices[np.argsort(self.tgt_sizes[indices], kind='mergesort')]

        return indices[np.argsort(self.src_sizes[indices], kind='mergesort')]



    def valid_size(self, index, max_positions):
        """Check if an example's size is valid according to max_positions."""
        max_source_positions, max_target_positions = self._get_max_positions(max_positions)

        return (
            self.src_sizes[index] <= max_source_positions
            and (self.tgt_sizes is None or self.tgt_sizes[index] <= max_target_positions)
        )


    def _get_max_positions(self, max_positions):
        if max_positions is None:
            return self.max_source_positions, self.max_target_positions

        assert len(max_positions) == 2

        max_src_pos, max_tgt_pos = max_positions

        return min(self.max_source_positions, max_src_pos), min(self.max_target_positions, max_tgt_pos)


def collater_isolated(samples, seq_len_multiple, left_pad_source, left_pad_target):
    """Merge a list of samples to form a mini-batch."""
    return collate(
        samples,
        pad_idx=1,
        eos_idx=2,
        left_pad_source=left_pad_source,
        left_pad_target=left_pad_target,
        bsz_mult=8,
        seq_len_multiple=seq_len_multiple,
    )


def get_dummy_batch_isolated(max_tokens_per_batch, max_positions, seq_len_multiple):
    '''Creates a dummy batch'''
    max_source_positions, max_target_positions = max_positions[0], max_positions[1]
    src_len, tgt_len = max_source_positions, max_target_positions
    n_seq_per_batch_based_on_longest_seq = max_tokens_per_batch // max(src_len, tgt_len)

    nspecial = 3
    ntok_alloc = 33712
    eos_id = 2
    dummy_seq_src = torch.Tensor(src_len).uniform_(nspecial + 1, ntok_alloc).long()
    dummy_seq_src[-1] = eos_id

    dummy_seq_tgt = torch.Tensor(tgt_len).uniform_(nspecial + 1, ntok_alloc).long()
    dummy_seq_tgt[-1] = eos_id

    return collater_isolated([
        {
            'id': i,
            'source': dummy_seq_src,
            'target': dummy_seq_tgt
        }
        for i in range(n_seq_per_batch_based_on_longest_seq)
    ],
    seq_len_multiple,
    left_pad_source=True,
    left_pad_target=False,
    )