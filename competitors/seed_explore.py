import datetime
import random
import copy
import pathlib

import math
import os

from seqsamphill.utils import read_data, read_data_kosarak, uct, \
    is_subsequence, sequence_mutable_to_immutable, print_results, \
    read_data_sc2, k_length, generate_bitset, following_ones, \
    get_support_from_vector, compute_first_zero_mask, compute_last_ones_mask, \
    count_target_class_data, extract_items, compute_WRAcc, compute_WRAcc_vertical, jaccard_measure, find_LCS, \
    reduce_k_length, average_results

from seqsamphill.priorityset import PrioritySet, THETA


def compute_variations_better_wracc(sequence, items, data, target_class,
                                    bitset_slot_size,
                                    itemsets_bitsets, class_data_count,
                                    first_zero_mask,
                                    last_ones_mask, target_wracc,
                                    enable_i=False, wracc_vertical=True):
    '''
    Compute variations until quality increases
    :param sequence:
    :param items: the list of all possible items
    :return: the best new element (sequence, wracc), or None if we are on a local optimum
    '''
    variations = []

    for itemset_i, itemset in enumerate(sequence):
        # i_extension
        if enable_i:
            for item_possible in items:
                new_variation_i_extension = copy.deepcopy(sequence)
                new_variation_i_extension[itemset_i].add(item_possible)

                if wracc_vertical:
                    new_variation_i_wracc, new_variation_i_bitset = compute_WRAcc_vertical(data,
                                                                                           new_variation_i_extension,
                                                                                           target_class,
                                                                                           bitset_slot_size,
                                                                                           itemsets_bitsets,
                                                                                           class_data_count,
                                                                                           first_zero_mask,
                                                                                           last_ones_mask)
                else:
                    new_variation_i_wracc = compute_WRAcc(data, new_variation_i_extension, target_class)
                    new_variation_i_bitset = 0

                variations.append(
                    (new_variation_i_extension, new_variation_i_wracc, new_variation_i_bitset))

                if new_variation_i_wracc > target_wracc:
                    return variations[-1]

        # s_extension
        for item_possible in items:
            new_variation_s_extension = copy.deepcopy(sequence)
            new_variation_s_extension.insert(itemset_i, {item_possible})

            if wracc_vertical:
                new_variation_s_wracc, new_variation_s_bitset = compute_WRAcc_vertical(data,
                                                                                       new_variation_s_extension,
                                                                                       target_class,
                                                                                       bitset_slot_size,
                                                                                       itemsets_bitsets,
                                                                                       class_data_count,
                                                                                       first_zero_mask,
                                                                                       last_ones_mask)
            else:
                new_variation_s_wracc = compute_WRAcc(data,
                                                      new_variation_s_extension,
                                                      target_class)
                new_variation_s_bitset = 0

            variations.append(
                (new_variation_s_extension, new_variation_s_wracc, new_variation_s_bitset))

            if new_variation_s_wracc > target_wracc:
                return variations[-1]

        for item_i, item in enumerate(itemset):
            new_variation_remove = copy.deepcopy(sequence)

            # we can switch this item, remove it or add it as s or i-extension

            if (k_length(sequence) > 1):
                new_variation_remove[itemset_i].remove(item)

                if len(new_variation_remove[itemset_i]) == 0:
                    new_variation_remove.pop(itemset_i)

                if wracc_vertical:
                    new_variation_remove_wracc, new_variation_remove_bitset = compute_WRAcc_vertical(data,
                                                                                                     new_variation_remove,
                                                                                                     target_class,
                                                                                                     bitset_slot_size,
                                                                                                     itemsets_bitsets,
                                                                                                     class_data_count,
                                                                                                     first_zero_mask,
                                                                                                     last_ones_mask)
                else:
                    new_variation_remove_wracc = compute_WRAcc(data,
                                                               new_variation_remove,
                                                               target_class)
                    new_variation_remove_bitset = 0

                variations.append(
                    (new_variation_remove, new_variation_remove_wracc, new_variation_remove_bitset))
                if new_variation_remove_wracc > target_wracc:
                    return variations[-1]

    # s_extension for last element
    for item_possible in items:
        new_variation_s_extension = copy.deepcopy(sequence)
        new_variation_s_extension.append({item_possible})

        if wracc_vertical:
            new_variation_s_wracc, new_variation_s_bitset = compute_WRAcc_vertical(data,
                                                                                   new_variation_s_extension,
                                                                                   target_class,
                                                                                   bitset_slot_size,
                                                                                   itemsets_bitsets,
                                                                                   class_data_count,
                                                                                   first_zero_mask,
                                                                                   last_ones_mask)
        else:
            new_variation_s_wracc = compute_WRAcc(data,
                                                  new_variation_s_extension,
                                                  target_class)
            new_variation_s_bitset = 0

        variations.append(
            (new_variation_s_extension, new_variation_s_wracc, new_variation_s_bitset))
        if new_variation_s_wracc > target_wracc:
            return variations[-1]

    return None


def generalize_sequence(sequence, data, target_class, bitset_slot_size,
                        itemsets_bitsets, class_data_count,
                        first_zero_mask,
                        last_ones_mask, wracc_vertical=True):
    sequence = copy.deepcopy(sequence)
    # we remove z items randomly
    seq_items_nb = len([i for j_set in sequence for i in j_set])
    z = random.randint(0, seq_items_nb - 1)
    for _ in range(z):
        chosen_itemset_i = random.randint(0, len(sequence) - 1)
        chosen_itemset = sequence[chosen_itemset_i]

        chosen_itemset.remove(random.sample(chosen_itemset, 1)[0])

        if len(chosen_itemset) == 0:
            sequence.pop(chosen_itemset_i)

    # now we compute the Wracc
    if wracc_vertical:
        wracc, bitset = compute_WRAcc_vertical(data, sequence, target_class,
                                               bitset_slot_size,
                                               itemsets_bitsets, class_data_count,
                                               first_zero_mask, last_ones_mask)
    else:
        wracc = compute_WRAcc(data, sequence, target_class)
        bitset = 0
    return sequence, wracc, bitset


def filter_target_class(data, target_class):
    filter_data = []
    for line in data:
        if line[0] == target_class:
            filter_data.append(line)

    return filter_data


def extract_best_elements_path(path, theta, bitset_slot_size, first_zero_mask, last_ones_mask, wracc_vertical=True):
    '''

    :param path: path in the form of (WRAcc, sequence, bitset)
    :param theta: similarity
    :return:
    '''
    try:
        best_wracc, best_sequence, best_bitset = path[-1]
    except:
        return []

    best_sequences = [(best_wracc, best_sequence)]

    # need to compare with each previous added element
    for wracc, sequence, bitset in reversed(path):
        if wracc_vertical:
            if jaccard_measure(bitset, best_bitset, bitset_slot_size, first_zero_mask, last_ones_mask) < theta:
                best_sequences.append((wracc, sequence))
                best_sequence, best_bitset = sequence, bitset
        else:
            best_sequences.append((wracc, sequence))
            best_sequences, best_bitset = sequence, bitset

    return best_sequences


def create_seed(data, target_class, data_target_class, bitset_slot_size, itemsets_bitsets, class_data_count,
                first_zero_mask, last_ones_mask):
    # sample
    sequence = copy.deepcopy(random.choice(data_target_class))
    sequence = sequence[1:]

    seed, quality, bitset = generalize_sequence(sequence,
                                                data,
                                                target_class,
                                                bitset_slot_size,
                                                itemsets_bitsets,
                                                class_data_count,
                                                first_zero_mask,
                                                last_ones_mask)

    return (seed, quality, bitset)


def UCB(x, t, ni):
    '''
    :param t: iteration number
    :param ni: number of times current arm has been playedk
    :return:
    '''
    return x + math.sqrt((2 * math.log2(t)) / ni)

def UCB_diff(x, t, ni, diff):
    # we foster best element, and give advantage to elements with a big diff
    # return x + diff * 0.25 + math.sqrt((2 * math.log2(t)) / ni)
    return diff * 0.25

def select_arm(seeds, iterations_count):
    best_seed = ()
    best_score = -float('inf')

    for original_seed, (mean, ti, variation, _, diff) in seeds.items():
        score_compute = UCB_diff(mean, ti, iterations_count, diff)
        if score_compute > best_score:
            best_score = score_compute
            best_seed = original_seed

    return best_seed

def seed_explore(data, items, time_budget, target_class, top_k=10, enable_i=True):
    # TODO: normalize quality !
    # TODO: improve memory strategy
    # first term exploitation, second exploration: if last increase is weak, give less points. If all last elements are weak, remove element.
    # multi arms bandit, infinite arms, increasing reward. WRAcc normalize with better estimation than 0.25 !

    begin = datetime.datetime.utcnow()
    time_budget = datetime.timedelta(seconds=time_budget)

    data_target_class = filter_target_class(data, target_class)

    sorted_patterns = PrioritySet(top_k)

    # removing class
    bitset_slot_size = len(max(data, key=lambda x: len(x))) - 1
    first_zero_mask = compute_first_zero_mask(len(data), bitset_slot_size)
    last_ones_mask = compute_last_ones_mask(len(data), bitset_slot_size)
    class_data_count = count_target_class_data(data, target_class)
    itemsets_bitsets = {}

    iterations_count = 1
    optima_nb = 0
    # {original_seed: (quality, ti, variation, bitset, diff)} diff with preceding value
    seeds = {}

    while datetime.datetime.utcnow() - begin < time_budget:
        #if len(seeds) <= math.sqrt(iterations_count):
        if len(seeds) < top_k:
            seed, quality, bitset = create_seed(data, target_class, data_target_class, bitset_slot_size,
                                                itemsets_bitsets, class_data_count,
                                                first_zero_mask, last_ones_mask)

            seed_immu = sequence_mutable_to_immutable(seed)
            seeds[seed_immu] = (quality, 1, seed, bitset, 0)
            sorted_patterns.add(seed_immu, quality)

        else:
            best_origin_seed = select_arm(seeds, iterations_count)
            quality, ti, best_seed, bitset_best_seed, diff_quality = seeds[best_origin_seed]

            try:
                improved_best_seed, best_quality, best_bitset = compute_variations_better_wracc(best_seed,
                                                                                                items, data,
                                                                                                target_class,
                                                                                                bitset_slot_size,
                                                                                                itemsets_bitsets,
                                                                                                class_data_count,
                                                                                                first_zero_mask,
                                                                                                last_ones_mask,
                                                                                                quality,
                                                                                                enable_i)

                sorted_patterns.add(sequence_mutable_to_immutable(improved_best_seed), best_quality)


                seeds[best_origin_seed] = (best_quality, ti + 1, improved_best_seed, best_bitset, best_quality - quality)

            except TypeError:
                # we found a local optima
                #print('Found optima !')
                optima_nb += 1
                del seeds[best_origin_seed]

        iterations_count += 1

    print('Seed_Explore iterations:{}, {} optima and {} seeds'.format(iterations_count, optima_nb, len(seeds)))

    return sorted_patterns.get_top_k_non_redundant(data, top_k)


def launch():
    # DATA = read_data_sc2('../data/sequences-TZ-45.txt')[:500]
    DATA = read_data(pathlib.Path(__file__).parent.parent / 'data/promoters.data')

    # DATA = read_data_kosarak('../data/debile.data')
    # DATA_i = reduce_k_length(5, DATA)

    ITEMS = extract_items(DATA)

    results = seed_explore(DATA, ITEMS, 10, '+', top_k=10, enable_i=True)
    print_results(results)


if __name__ == '__main__':
    launch()