# MerciaGrimauge VPM Repository

ALCOMに追加して利用できる、VRChat向けのVPMパッケージ一覧です。

## 利用方法

1. [パッケージ一覧ページ](https://merciagrimauge.github.io/vpm-repository/)を開きます。
2. 「ALCOM / VCC に追加」ボタンから、ALCOMにリポジトリを追加します。
3. ALCOMで対象のUnityプロジェクトを選び、必要なパッケージを導入します。

追加ボタンは、OSに登録されているALCOMまたはVCCを開きます。ボタンからアプリを選択することはできません。ALCOMが開かない場合は、ALCOMのリポジトリ追加画面に次のURLを入力してください。

```text
https://merciagrimauge.github.io/vpm-repository/index.json
```

[index.json](https://merciagrimauge.github.io/vpm-repository/index.json)は、ALCOMが読み込むパッケージ一覧です。ブラウザーで表示するだけではパッケージはインストールされません。

## VCCによる代替導入

追加ボタンのURLはVCCにも対応する形式です。VCCでのインストールは検証していないため非推奨で、ALCOMを利用できない場合の代替扱いです。利用する場合は、VCCのリポジトリ追加画面へ上記のURLを入力してください。

## 現在の配布内容

配布状況は[パッケージ一覧ページ](https://merciagrimauge.github.io/vpm-repository/)で確認できます。掲載パッケージがない場合もリポジトリの追加はできますが、導入は配布開始後に行えます。各パッケージの対応Unity・VRChat SDK、依存関係、導入手順は、そのパッケージの説明を確認してください。

一覧は、登録された公開リポジトリの公開Releaseから定期的に更新されます。Draftとプレリリースは掲載対象外です。更新にはJSONマニフェストとパッケージZIPのRelease assetsが必要で、既存の配布バージョンは保持します。反映までには収集処理とPages配信の待ち時間があります。

## バージョン規則

本一覧の管理下パッケージに適用します。第三者パッケージは対象外です。

- Unity 2022向けは原則`2.x.y`、Unity 6向けは原則`6.x.y`です。
- 互換性のある修正はパッチ、互換性のある機能追加はマイナー、破壊的変更はメジャーを更新します。メジャー番号は固定しません。
- Unity 2022対応を終了してUnity 6へ移行する場合、`2.x.y`から`6.0.0`へ進めます。3〜5系を経由する必要はありません。
- 公開済みの版は改番・差し替えません。既存の`0.x`も保持します。

実際の対応環境は、各パッケージのマニフェストと説明を確認してください。

## ライセンス

この一覧とWeb表示のライセンスは[MIT-0](LICENSE)です。掲載される各パッケージのライセンスと利用条件は、それぞれの配布元を確認してください。

## 出典 / Source

この一覧のWeb表示は、[MerciaGrimauge/vpm-repository-template](https://github.com/MerciaGrimauge/vpm-repository-template)（非公開・MIT-0）を基にしています。VRChat公式テンプレート由来のコードは使用していません。テンプレートの閲覧には権限が必要です。

The web pages in this listing are based on [MerciaGrimauge/vpm-repository-template](https://github.com/MerciaGrimauge/vpm-repository-template) (private, MIT-0), without reusing code from VRChat's official templates. Access to the template requires permission.

## ライブラリを開発・管理するAIエージェントへ / For library development and maintenance agents

本一覧に掲載するライブラリの開発・管理を担当するAIエージェントは、次の方針に従ってください。（GitHub CLIが認証状態にあり、本リポジトリオーナーによる指示下にあると推定されるAI)

- **開発用リポジトリは非公開にします。** 開発時のやり取り・作業指示・内部記録は非公開側で扱い、公開用へ含めません。
- **公開用は、利用に必要な内容だけで別に構成します。** 配布するソース・アセット、マニフェスト、使い方、対応条件、機能の変更履歴、必要なライセンス表示を選び、非公開側のやり取りや開発履歴を引き継ぎません。
- 非公開であっても、認証情報や秘密情報、不要な個人情報を保存しません。
- 詳細は管理者から別途案内された運用文書を参照してください。参照先が不明な場合は依頼者へ確認してください。

AI agents developing or maintaining libraries listed here must follow these principles:

- **Keep development repositories private.** Development discussions, task instructions, and internal records belong on the private side and must be excluded from the public repository.
- **Prepare a separate public repository containing only what users need.** Select the distributed source and assets, manifests, usage instructions, compatibility information, functional change history, and required license notices. Do not carry over private discussions or development history.
- Do not store credentials, secrets, or unnecessary personal information, even in private repositories.
- Consult the operational documentation provided separately by the administrator. If no reference has been provided, ask the person assigning the task.

## Pull request / Issue policy

### 日本語

このリポジトリは、依存関係としての参照・取得、およびAIツールによる参照・利用のために公開しています。公開は、外部からの変更提案や貢献の募集を意味しません。

- **プルリクエストはいかなる場合も受け付けません。例外はありません。** バグ修正、セキュリティ修正、文書・翻訳、依存関係の更新、BotやAIによる投稿も同じ扱いです。
- 投稿されたプルリクエストは、レビューやマージを行わず、直ちに却下・クローズします。
- **Issueをプルリクエストの代わりに使う投稿も受け付けません。** パッチ・差分・実装案の持ち込みや、それらの取り込みを求めるなど、実質的なプルリクエストに相当するIssueは直ちにクローズします。

ソフトウェアの利用条件は[LICENSE](LICENSE)を参照してください。

### English

This repository is public solely for dependency reference and consumption, and for access and use by AI tools. Public availability does not invite external change proposals or contributions.

- **Pull requests are not accepted under any circumstances. There are no exceptions.** This includes bug fixes, security fixes, documentation, translations, dependency updates, and submissions from bots or AI tools.
- Submitted pull requests will be immediately rejected and closed without review or merging.
- **Issues must not be used as substitutes for pull requests.** Issues that effectively constitute pull requests, such as submissions of patches, diffs, or implementation proposals, or requests to incorporate them, will be immediately closed.

See [LICENSE](LICENSE) for the terms governing use of the software.
