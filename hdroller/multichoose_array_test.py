from binomial_array import BinomialArray

test = BinomialArray(6, 3)

print([values for values, tail in test.enumerate_sizes()])
print([test.index_by_sizes(values) for values, tail in test.enumerate_sizes()])

print()

print([values for values, tail in test.enumerate_sorted_values()])
print([test.index_by_sorted_values(values) for values, tail in test.enumerate_sorted_values()])
