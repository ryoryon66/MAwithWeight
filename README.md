# MAwithWeight
MAモデルに重みをつけたものの実装

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

赤色の辺がattack,青色の辺がsupportです。

<img width="738" alt="スクリーンショット 2023-03-29 18 24 16" src="https://user-images.githubusercontent.com/46624038/228489370-ff55d57c-94b7-4f99-be98-eb1faba8742a.png">
<img width="740" alt="スクリーンショット 2023-03-29 18 24 33" src="https://user-images.githubusercontent.com/46624038/228489550-e470e432-61dd-489b-8d7d-bff74ed5ae1e.png">
<img width="811" alt="スクリーンショット 2023-03-29 18 25 00" src="https://user-images.githubusercontent.com/46624038/228489645-23824f74-6798-4db4-a520-bce23e5bd6c9.png">

# 重みの予測ラベル計算への算入方法

条件データ (+,x1,x2) (-,y1,y2)が付与された頂点uの予測ラベルは以下のように定まる。

- Au : Auをrejに向かわせるような頂点の集合 (ラベルがl1かつuをattack　または　ラベルがl2かつuをsupport)
- Bu : Auをaccに向かわせるような頂点の集合 (ラベルがl2かつuをattack　または　ラベルがl1かつuをsupport)

V : AuとBuを一緒にした多重集合

average_weight : V内の頂点の重みの平均

としたとき

- A_weightはAu内の重みの合計をaverage_weightで除したもの
- B_weightはBu内の重みの合計をaverage_weightで除したもの

で定める。

- (+,x1,x2)についてはx1,x2,B_weightの大小関係によって判断を定める.
- (-,y1,y2)についてはy1,y2,A_weightの大小関係によって判断を定める。

以上の判断を総合して予測ラベルを定める(ソースコード内のtable_neutralなどを参照)。





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
