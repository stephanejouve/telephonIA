# CHANGELOG

<!-- version list -->

## v1.7.1 (2026-04-23)

### Bug Fixes

- **bundle**: Detecte PyInstaller via _MEIPASS et logge la resolution ffmpeg
  ([`d89fa52`](https://github.com/stephanejouve/telephonIA/commit/d89fa52e0c460c780772c8b6037cc204d894d850))


## v1.7.0 (2026-04-21)

### Bug Fixes

- **release**: Align publish-action sur v10.5.3 (version identique a semantic-release)
  ([#36](https://github.com/stephanejouve/telephonIA/pull/36),
  [`1031e27`](https://github.com/stephanejouve/telephonIA/commit/1031e274635bb285358daf4d58b3990cb11ad2e4))

- **release**: GitHub App token bypass branch protection main
  ([#36](https://github.com/stephanejouve/telephonIA/pull/36),
  [`1031e27`](https://github.com/stephanejouve/telephonIA/commit/1031e274635bb285358daf4d58b3990cb11ad2e4))

- **release**: GitHub App token pour bypass branch protection main
  ([#36](https://github.com/stephanejouve/telephonIA/pull/36),
  [`1031e27`](https://github.com/stephanejouve/telephonIA/commit/1031e274635bb285358daf4d58b3990cb11ad2e4))

- **release**: Remet fetch-depth: 0 (requis par PSR pour walker l'historique)
  ([#36](https://github.com/stephanejouve/telephonIA/pull/36),
  [`1031e27`](https://github.com/stephanejouve/telephonIA/commit/1031e274635bb285358daf4d58b3990cb11ad2e4))

- **release**: Retire fetch-depth: 0 (PSR v10.5+ deshallow auto)
  ([#36](https://github.com/stephanejouve/telephonIA/pull/36),
  [`1031e27`](https://github.com/stephanejouve/telephonIA/commit/1031e274635bb285358daf4d58b3990cb11ad2e4))

### Code Style

- Black + isort format auto sur paths.py + test_paths.py (line-length=100)
  ([#34](https://github.com/stephanejouve/telephonIA/pull/34),
  [`12e02c4`](https://github.com/stephanejouve/telephonIA/commit/12e02c4e0a86070531c08c3f7bfb0d2b68e12689))

### Continuous Integration

- Codecov v5 + windows spec guardrail + macOS py2app sanity
  ([#34](https://github.com/stephanejouve/telephonIA/pull/34),
  [`12e02c4`](https://github.com/stephanejouve/telephonIA/commit/12e02c4e0a86070531c08c3f7bfb0d2b68e12689))

- Codecov.yml (thresholds + ignore paths) + README badges CI & codecov
  ([#34](https://github.com/stephanejouve/telephonIA/pull/34),
  [`12e02c4`](https://github.com/stephanejouve/telephonIA/commit/12e02c4e0a86070531c08c3f7bfb0d2b68e12689))

- Fix secret name CODECOV_TOKEN -> CODECOV_TOKEN_TELEPHONIA
  ([#34](https://github.com/stephanejouve/telephonIA/pull/34),
  [`12e02c4`](https://github.com/stephanejouve/telephonIA/commit/12e02c4e0a86070531c08c3f7bfb0d2b68e12689))

- Refresh poetry.lock pour suivre l'ajout [tool.coverage] dans pyproject
  ([#34](https://github.com/stephanejouve/telephonIA/pull/34),
  [`12e02c4`](https://github.com/stephanejouve/telephonIA/commit/12e02c4e0a86070531c08c3f7bfb0d2b68e12689))

- Revert to CODECOV_TOKEN (secret auto-provisioned par Codecov app)
  ([#34](https://github.com/stephanejouve/telephonIA/pull/34),
  [`12e02c4`](https://github.com/stephanejouve/telephonIA/commit/12e02c4e0a86070531c08c3f7bfb0d2b68e12689))

### Features

- **bundle**: Embed ffmpeg+ffprobe, icons, py2app macOS bundle, LGPL attribution
  ([#33](https://github.com/stephanejouve/telephonIA/pull/33),
  [`b9510c3`](https://github.com/stephanejouve/telephonIA/commit/b9510c32ac6c3b39dc488cab25e1e2822cfc4956))

- **release**: Ffprobe download + SLSA attestation + fix GH_TOKEN -> GITHUB_TOKEN
  ([#35](https://github.com/stephanejouve/telephonIA/pull/35),
  [`0adf8c6`](https://github.com/stephanejouve/telephonIA/commit/0adf8c6dc64ac4151b4bdf7454ce42d42f9cc22a))

### Testing

- **web_api**: Skip 5 tests sur fixtures MP3/WAV synthetiques non-parsables par ffmpeg
  ([#34](https://github.com/stephanejouve/telephonIA/pull/34),
  [`12e02c4`](https://github.com/stephanejouve/telephonIA/commit/12e02c4e0a86070531c08c3f7bfb0d2b68e12689))


## v1.6.0 (2026-04-09)

### Documentation

- Ajouter commande PowerShell et note VPN au README
  ([`35a9506`](https://github.com/stephanejouve/telephonIA/commit/35a95066141193bc00dd3c337c41b683ac834838))

### Features

- Ajouter identifiant de lot pour prefixer les fichiers WAV generes
  ([#32](https://github.com/stephanejouve/telephonIA/pull/32),
  [`c00be1a`](https://github.com/stephanejouve/telephonIA/commit/c00be1a5af0507208b88c03284c1a59cabc93194))


## v1.5.0 (2026-03-30)

### Documentation

- Mettre a jour le README avec toutes les fonctionnalites
  ([#30](https://github.com/stephanejouve/telephonIA/pull/30),
  [`b08cbfe`](https://github.com/stephanejouve/telephonIA/commit/b08cbfeaf1085e0fbf5cbd9423293d4b0d7db7c4))

### Features

- Normaliser les URLs et termes web pour la prononciation francaise TTS
  ([#30](https://github.com/stephanejouve/telephonIA/pull/30),
  [`b08cbfe`](https://github.com/stephanejouve/telephonIA/commit/b08cbfeaf1085e0fbf5cbd9423293d4b0d7db7c4))

- Normaliser les URLs pour la prononciation francaise TTS
  ([#30](https://github.com/stephanejouve/telephonIA/pull/30),
  [`b08cbfe`](https://github.com/stephanejouve/telephonIA/commit/b08cbfeaf1085e0fbf5cbd9423293d4b0d7db7c4))


## v1.4.10 (2026-03-29)

### Bug Fixes

- **web**: Ajouter .g729 au file picker et retirer les print() debug
  ([#29](https://github.com/stephanejouve/telephonIA/pull/29),
  [`6c1ee91`](https://github.com/stephanejouve/telephonIA/commit/6c1ee916e4590426f57669546fea6cc5467f6a63))


## v1.4.9 (2026-03-29)

### Bug Fixes

- Ajout print() debug dans upload_audio (visible dans console exe)
  ([#28](https://github.com/stephanejouve/telephonIA/pull/28),
  [`e776b17`](https://github.com/stephanejouve/telephonIA/commit/e776b17f7c3a3d69a4e2c4c0502c44773db862ac))


## v1.4.8 (2026-03-29)

### Bug Fixes

- Import G.729 ne detruit plus la musique de fond
  ([#27](https://github.com/stephanejouve/telephonIA/pull/27),
  [`6b4869f`](https://github.com/stephanejouve/telephonIA/commit/6b4869fa190f3bc0d196a2b5c0295a1684813fbb))


## v1.4.7 (2026-03-29)

### Bug Fixes

- **api**: Persister music_path dans messages.json (source unique de verite)
  ([#26](https://github.com/stephanejouve/telephonIA/pull/26),
  [`666adc3`](https://github.com/stephanejouve/telephonIA/commit/666adc3324ed6c5a063ca4aa22eaeb05937d3297))


## v1.4.6 (2026-03-29)

### Bug Fixes

- **api**: Rendre la suppression musique non-bloquante a l'import G.729
  ([#25](https://github.com/stephanejouve/telephonIA/pull/25),
  [`af32d1f`](https://github.com/stephanejouve/telephonIA/commit/af32d1fe1ca2dcd80da086fed7972d37fcb78bad))


## v1.4.5 (2026-03-29)

### Bug Fixes

- **generator**: Utiliser self.music_path au lieu de get_music_path()
  ([#24](https://github.com/stephanejouve/telephonIA/pull/24),
  [`d539472`](https://github.com/stephanejouve/telephonIA/commit/d53947248dfe92087cba49b9869c2ba68ff05cb9))


## v1.4.4 (2026-03-29)

### Bug Fixes

- **api**: Supprimer la musique dans tous les emplacements a l'import G.729
  ([#23](https://github.com/stephanejouve/telephonIA/pull/23),
  [`5d97e6e`](https://github.com/stephanejouve/telephonIA/commit/5d97e6ebc0d55abe0c3b422762aa0902b90bf08d))


## v1.4.3 (2026-03-29)

### Bug Fixes

- **api**: Supprimer physiquement la musique a l'import G.729
  ([#22](https://github.com/stephanejouve/telephonIA/pull/22),
  [`00f6214`](https://github.com/stephanejouve/telephonIA/commit/00f6214fe6740f0fc175f9fc9f3b2196faf67014))


## v1.4.2 (2026-03-29)

### Bug Fixes

- **api**: Desactiver la musique de fond a l'import G.729
  ([#21](https://github.com/stephanejouve/telephonIA/pull/21),
  [`0236e41`](https://github.com/stephanejouve/telephonIA/commit/0236e4174a569dd08d91ef8314ec5ef331a9d01f))


## v1.4.1 (2026-03-29)

### Bug Fixes

- **api**: Exclure les messages G.729 importes de la generation TTS
  ([#20](https://github.com/stephanejouve/telephonIA/pull/20),
  [`38771b5`](https://github.com/stephanejouve/telephonIA/commit/38771b5c39598499e22af7b796c309f07fa6f1e8))


## v1.4.0 (2026-03-29)

### Features

- **web**: Confirmation ecrasement G.729 et lien telecharger
  ([#19](https://github.com/stephanejouve/telephonIA/pull/19),
  [`21e57a3`](https://github.com/stephanejouve/telephonIA/commit/21e57a3b079f7ad333695ed3ace68a47ea6407c7))


## v1.3.0 (2026-03-29)

### Bug Fixes

- **ci**: Utiliser GH_TOKEN pour bypasser la protection de branche
  ([`285304e`](https://github.com/stephanejouve/telephonIA/commit/285304efbf092242ebcaca2a9ed7f0c311ae6ea6))

### Features

- **web**: Import audio existant, selecteur de voix et suppression audio
  ([#17](https://github.com/stephanejouve/telephonIA/pull/17),
  [`3b64116`](https://github.com/stephanejouve/telephonIA/commit/3b64116457cd37c060a7bfc5421af19411a884a6))


## v1.2.1 (2026-03-29)

### Bug Fixes

- Empecher le cache navigateur sur les fichiers audio
  ([#16](https://github.com/stephanejouve/telephonIA/pull/16),
  [`3b0aede`](https://github.com/stephanejouve/telephonIA/commit/3b0aede9678265d56b526b313d019d4b5f723113))


## v1.2.0 (2026-03-29)

### Features

- Outro musique d'une mesure apres la voix
  ([#15](https://github.com/stephanejouve/telephonIA/pull/15),
  [`bb7e5f3`](https://github.com/stephanejouve/telephonIA/commit/bb7e5f39c932f90d4c1c7eaf5f84b1b5e6549d39))


## v1.1.0 (2026-03-29)

### Features

- Intro musique d'une mesure et mixage sur les 3 messages
  ([#14](https://github.com/stephanejouve/telephonIA/pull/14),
  [`a0b76fa`](https://github.com/stephanejouve/telephonIA/commit/a0b76fade99778cd6bcb81081504005c30741ff6))


## v1.0.0 (2026-03-29)

### Continuous Integration

- Ajout semantic-release et workflow de release automatique
  ([`7c3a550`](https://github.com/stephanejouve/telephonIA/commit/7c3a550e9107f2eb8cca7f5a5ff50fd203760d77))


## v0.1.0 (2026-03-29)

- Initial Release
