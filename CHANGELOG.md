# Change Log
All notable changes to this project will be documented in this file.

20220902以前の変更は[フォーク元のリポジトリ](https://github.com/kamimiya/yomiage_VOICEVOX)を参照してください。

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