# MAwithWeight
MAモデルにweightをつけたバージョンの実装例


# 環境構築

python 3.9.9で動作確認をしています。

```
git clone https://github.com/ryoryon66/MAwithWeight.git
cd MAwithWeight
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

M1 macでpygraphvizのinstallに失敗する場合こちらが参考になります。[link](https://github.com/pygraphviz/pygraphviz/issues/398)

```
python MAmodel/MAmodel.py
```

が動作し、pdfファイルが生成されていれば環境構築終了です。

# 使い方

1. sample_model/ma1model.ymlの形式を参考にして重み付きMAモデルを表現するymlファイルを書いてください。
2. MAmodel/settings.pyを適切に設定してください。
3. python MAmodel/MAmodel.pyを実行してください。

# 可視化例

<img width="738" alt="スクリーンショット 2023-03-29 18 24 16" src="https://user-images.githubusercontent.com/46624038/228489370-ff55d57c-94b7-4f99-be98-eb1faba8742a.png">
<img width="740" alt="スクリーンショット 2023-03-29 18 24 33" src="https://user-images.githubusercontent.com/46624038/228489550-e470e432-61dd-489b-8d7d-bff74ed5ae1e.png">
<img width="811" alt="スクリーンショット 2023-03-29 18 25 00" src="https://user-images.githubusercontent.com/46624038/228489645-23824f74-6798-4db4-a520-bce23e5bd6c9.png">




# グラフにつけた属性一覧(networkX)



MAモデル

graph

- label_list : 用いるラベルのリスト [l1,l2,l3]


edge

- attack : boolでTrueならattack,Falseならsupport
- color : グラフ描画の時の色。

node

- label ラベリングデータによって付けられたラベル

- predicted_labels 周囲の頂点から予測されたラベルのリスト

- judges : 条件ごとの判断などを並べたもの.Aが大きいほどrejされやすく、Bが大きいほどaccされやすくなる。Aは(-,x,y),Bは(+,x,y)の条件判断に用いられる
