# Change Log
All notable changes to this project will be documented in this file.

20220902以前の変更は[フォーク元のリポジトリ](https://github.com/kamimiya/yomiage_VOICEVOX)を参照してください。

## 0.1.0（2026-11-10）
全体を作り直したバージョンです。旧バージョンの設定とデータは引き継げません。

### Added
- Voicepeak と VoiSona Talk に対応
- DAVE（音声のE2E暗号化）に対応
- `!` コマンドとスラッシュコマンドを同じ実装で受けるように変更し、話者とパラメータの入力に自動補完を追加
- GitHub Actions によるリリース作成（LGPL ビルドの FFmpeg を同梱）
- LICENSE と THIRD_PARTY_NOTICES.md

### Changed
- 設定ファイルを `setting.ini` から `config.toml` に変更
- 保存データを CSV から SQLite に変更
- スラッシュコマンドのグループを廃止（`/voice-bot1 join` → `/join`）
- `!chg_my_voice` の引数を `ソフト名 話者 スタイル` の順に変更し、ソフト名を必須に変更
- 音声の合成と再生を分離し、合成中も Bot が応答するように変更
- URL の読み上げを「URL」に変更
- 添付ファイルが複数ある場合は、種類ごとに1回読み上げるように変更
- 単語帳の置換で、置換後の読みがさらに置換されないように変更
- 全員が退出したときの自動退出が、入退室の通知の設定に関係なく動くように変更

### Fixed
- `!stop` で再生が止まらない不具合
- `!help` と `!hello` が正しく表示されない不具合
- `!chg_voice_setting` がエラーになる不具合
- コードブロックと伏せ字の置換が正しく動かない場合がある不具合
- スタンプと添付ファイルが先頭の1件しか処理されない不具合

### Removed
- 名前読み上げ（`!read_name`）
- Bot のステータスに接続中のVC名を表示する機能（`!inform_tmp_room`）
- リポジトリ内の実行ファイルとバッチファイル

## 20230613
### Fixed
デフォルトスタイルが利用できない時に読み上げが行われなくなる不具合の修正

## 20230611
### Fixed
入退室時の読み上げの際、ニックネームではなく新方式のユーザー名が読み上げられる不具合の修正

## 20230604
### Added
- COEIROINKv2対応

### Fixed
- A.I.VOICEで読み上げるときに絵文字のみをチャットすると読み上げがおかしくなる不具合の修正

### Changed
- バッチファイルのディレクトリの変更
- setting.iniの書式変更（CoeiroinkV2 Settingセクションの追加）
- 更新履歴をCHANGELOG.mdに分離

## 20230603
### Fixed
- 使用しない設定のソフトのデータが起動時に消去される不具合の修正

## 20230518
### Fixed
- A.I.VOICEのコネクションタイムアウトが考慮されていない不具合の修正

## 20230516
### Added
- A.I.VOICE対応

### Changed
- setting.iniの書式変更（A.I.VOICE Settingセクションの追加）
- スタイル毎のパラメータ周りについて内部的な仕様変更
- 異なるソフトウェアにキャラ名とスタイル名が同じボイスが存在する場合にそれぞれ別のパラメータを適用できるように変更
- style_setting.csvの書式変更

## 20230327
### Fixed
- Discord APIの仕様変更への対応

## 20221221
### Added
- スラッシュコマンド対応

### Fixed
- ロールに対するメンションが正しく読み上げられない不具合を修正
- ユーザーIDに紐づいているボイススタイルが利用できない場合、直前に生成したwavファイルが再生される不具合の修正

## 20221215
### Changed
- setting.iniの[Using Setting]セクションの書式変更

### Removed
- readmeから現在のバージョンで実装されていないSE関連の文言を削除

## 20221002
### Changed
- 設定ファイルの名称変更
- 各種リストのロケーションを設定ファイルで指定するように変更

## 20220924
### Added
- スタイル毎に話速・音高・抑揚・音量を変更可能に

## 20220923
### Added
- COEIROINK, LMROID, SHAREVOX対応
- 話者の動的取得

### Changed
- voice_list.csvの書式変更