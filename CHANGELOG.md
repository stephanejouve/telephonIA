# CHANGELOG

<!-- version list -->

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
