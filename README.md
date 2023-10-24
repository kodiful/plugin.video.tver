## Kodiアドオン：TVerクライアント

[Tver](https://tver.jp)を操作するためのKodiアドオンです。
macOSで動作検証しています。

### 目次

[ホーム画面と検索](#ホーム画面と検索)  
[アドオン設定](#アドオン設定)

### ホーム画面と検索

起動するとホーム画面が表示されます。

![ホーム画面](https://github.com/kodiful/plugin.video.tver/assets/12268536/58ddf8e5-3c88-4dea-a815-b37bfc58640c)

画面の各項目の内容は以下の通りです。

#### 検索：曜日

番組を検索します。曜日→チャンネル→ジャンルの順に検索条件を設定します。まず、曜日を選択します。

![曜日選択画面](https://user-images.githubusercontent.com/12268536/230548653-043125df-38e6-4b25-a0ad-3bcc76fe7ec1.png)

次にチャンネルを選択します。

![チャンネル選択画面](https://user-images.githubusercontent.com/12268536/230534980-f88bd3b0-891b-4505-8bfb-fe94c26aaf9c.png)

次にジャンルを選択します。

![ジャンル選択画面](https://user-images.githubusercontent.com/12268536/230535078-fb60aa9c-570e-41ee-b66f-4f1575912a24.png)

検索結果が表示されます。

![検索結果画面](https://user-images.githubusercontent.com/12268536/230535119-113b6dbf-ff04-460a-94ab-7ea189c9b398.png)

ここで見たい番組を選択すると、番組が再生されます（Kodiの設定によっては詳細情報が表示されます）。

#### 検索：チャンネル

検索条件を、チャンネル→ジャンル→曜日の順に設定するほかは「検索：曜日」と同様です。

#### 検索：ジャンル

検索条件を、ジャンル→チャンネル→曜日の順に設定するほかは「検索：曜日」と同様です。

### アドオン設定

サブメニューから「アドオン設定」を選択して、アドオン設定画面を表示します。

![アドオン設定画面](https://github.com/kodiful/plugin.video.tver/assets/12268536/018fa56c-b102-4cbb-9f36-3798b0bcfb39)

![アドオン設定画面](https://github.com/kodiful/plugin.video.tver/assets/12268536/71c0d7ae-4c83-4dd3-89d5-a1c7ddfdeaad)

画面の各項目の内容は以下の通りです。

#### サムネイルキャッシュをクリア

アドオンが生成した番組のサムネイルの容量が表示されます。必要に応じてクリアしてください。

#### デバッグ

デバッグ用の設定です。 動作に関する情報をKodiのログファイルに書き出します。
