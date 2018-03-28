#!/usr/bin/env python
# -*- coding: utf-8 -*-


from mctseq.sequencenode import SequenceNode
from mctseq.utils import sequence_mutable_to_immutable

data = [['+', {'A', 'B'}, {'C'}], ['-', {'A'}, {'B'}]]

def test_create_sequence():
    seq = SequenceNode([{'A'}, {'BC'}], None, {'A', 'B', 'C'}, data, '+', 0)
    assert seq != None


def test_possible_children():
    seq = SequenceNode([{'A'}, {'B'}], None, {'A', 'B'}, data, '+', 0)
    possible_children = seq.non_generated_children
    assert sequence_mutable_to_immutable(
        [{'A', 'B'}, {'B'}]) in possible_children
    assert len(possible_children) == 6
    # check if no duplicate
