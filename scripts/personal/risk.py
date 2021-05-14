def count_ordered_partitions(total, partitions):
    if partitions == 1: return 1
    result = 0
    for remainder in range(total+1):
        result += count_ordered_partitions(remainder, partitions-1)
    return result

print(count_ordered_partitions(10, 6))
