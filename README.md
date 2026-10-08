# MerciaGrimauge VPM Repository

VCC / ALCOM に追加して利用できる、VRChat向けのVPMパッケージ一覧です。

## 利用方法

1. [パッケージ一覧ページ](https://merciagrimauge.github.io/vpm-repository/)を開きます。
2. 「VCC / ALCOM に追加」ボタンから、使用しているアプリにリポジトリを追加します。
3. アプリで対象のUnityプロジェクトを選び、必要なパッケージを導入します。

追加ボタンでアプリが開かない場合は、VCCまたはALCOMのリポジトリ追加画面に、次のURLを入力してください。

```text
https://merciagrimauge.github.io/vpm-repository/index.json
```

[index.json](https://merciagrimauge.github.io/vpm-repository/index.json)は、VCC / ALCOMが読み込むパッケージ一覧です。ブラウザーで表示するだけではパッケージはインストールされません。

## 現在の配布内容

現在、公開されているパッケージはありません。

リポジトリの追加はできますが、パッケージの導入は配布開始後に行えます。配布される各パッケージの対応Unity・VRChat SDK、依存関係、導入手順は、そのパッケージの説明を確認してください。

## ライセンス

この一覧とWeb表示のライセンスは[MIT-0](LICENSE)です。掲載される各パッケージのライセンスと利用条件は、それぞれの配布元を確認してください。

## ライブラリを開発・管理するAIエージェントへ / For library development and maintenance agents

本一覧に掲載するライブラリの開発・管理を担当するAIエージェントは、次の方針に従ってください。

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
