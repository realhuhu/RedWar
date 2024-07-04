from pathlib import Path

import pandas as pd

root = Path(__file__).absolute().parents[2] / "data" / "web"

item = pd.read_csv(root / "Item.csv", header=None)
item.columns = item.iloc[1]
item = item.drop(0)
item = item.drop(1)
item = item.iloc[0:, 0: 2]
item_dictionary = {key: value for key, value in zip(item['物品ID(id)'], item['名称(name)'])}

reward = pd.read_csv(root / "GameReward.csv", header=None)
reward.fillna("", inplace=True)
reward.columns = reward.iloc[1]
reward = reward.drop(0)
reward = reward.drop(1)

reward_dictionary = {}

for _, i in list(reward.iterrows())[1:]:
    reward_id, _, _, _, _, _, a1, v1, a2, v2, a3, v3, a4, v4, *_ = i
    strings = []
    if a1:
        strings.append(f"{item_dictionary[a1]}*{v1}")
    if a2:
        strings.append(f"{item_dictionary[a2]}*{v2}")
    if a3:
        strings.append(f"{item_dictionary[a3]}*{v3}")
    if a4:
        strings.append(f"{item_dictionary[a4]}*{v4}")

    reward_dictionary[reward_id] = " ".join(strings)

tree = pd.read_csv(root / "ActiveChristmasWishTree.csv")
tree.columns = tree.iloc[0]
tree = tree.drop(0)

for i in [
    "1级树的奖励(item)",
    "2级树的奖励(item1)",
    "3级树的奖励(item2)",
    "4级树的奖励(item3)",
    "5级树的奖励(item4)",
    "6级树的奖励(item5)",
]:
    tree[i] = tree[i].apply(lambda x: item_dictionary.get(x, x))

for i in [
    "基础奖励(gamereward)",
    "黄金特权奖励(gamereward1)",
    "白金特权奖励(gamereward2)",
    "排名奖励(gamereward3)"
]:
    tree[i] = tree[i].apply(lambda x: reward_dictionary.get(x, x))

tree.to_excel("ActiveChristmasWishTree.xlsx", index=False)
