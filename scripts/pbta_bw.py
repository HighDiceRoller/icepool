from hdroller import Die

result = ''

base_bw_dice = 24
bw_scale = 2

for pbta_bonus in [-1, 0, 1, 2, 3]:
    num_bw_dice = int(bw_scale*pbta_bonus+base_bw_dice)
    bw_die = Die.coin(0.5).repeat_and_sum(num_bw_dice)
    pbta_high_chance = Die.d(2, 6) + pbta_bonus >= 11
    pbta_mid_chance = Die.d(2, 6) + pbta_bonus >= 7

    bw_target = base_bw_dice - (base_bw_dice // 2)
    bw_high_chance = bw_die >= bw_target + int(2*bw_scale)
    bw_mid_chance = bw_die >= bw_target

    result += '\t'.join(str(x) for  x in [
        pbta_bonus,
        num_bw_dice,
        pbta_mid_chance,
        bw_mid_chance,
        pbta_high_chance,
        bw_high_chance])
    result += '\n'

with open('output/pbta_bw.csv', mode='w') as outfile:
    outfile.write(result)
