# CHANGELOG

<!-- version list -->

## v1.3.5 (2026-09-03)

### Bug Fixes

- Drop GHA layer cache from the GHCR push build
  ([`96af8ce`](https://github.com/thentsation/sentiment-analysis-api/commit/96af8ced72b3d8dc13e95f809d29b097f89bfb1a))


## v1.3.4 (2026-09-03)

### Bug Fixes

- Use ETag-based optimistic concurrency for security list updates
  ([`841368d`](https://github.com/thentsation/sentiment-analysis-api/commit/841368dd46d7754e52ac9c645a0ff0c71b529da9))


## v1.3.3 (2026-09-03)

### Bug Fixes

- Preserve trailing newline when writing SSH key from secret
  ([`4d30adc`](https://github.com/thentsation/sentiment-analysis-api/commit/4d30adca1afb4c8045f8fec4c055e1491726b9c2))


## v1.3.2 (2026-09-03)

### Bug Fixes

- Update pip-audit command to ignore specific vulnerability
  ([`e62ad58`](https://github.com/ntsation/sentiment-analysis-api/commit/e62ad58a3348187b6b5a33eb9d3ad7ec8e99161c))

### Chores

- **deps**: Bump psycopg from 3.2.10 to 3.3.4 in /config
  ([`eac6ffc`](https://github.com/ntsation/sentiment-analysis-api/commit/eac6ffc90e16508cedefbf2ab366f9b2c2c55c57))


## v1.3.1 (2026-08-31)

### Bug Fixes

- Import Iterator from collections.abc to avoid redundancy
  ([`d20cffd`](https://github.com/ntsation/sentiment-analysis-api/commit/d20cffd2c13bab6d51a9e162e1c9a3ebbd34f492))

### Chores

- **ci**: Bump docker/build-push-action from 6 to 7
  ([`8dd662b`](https://github.com/ntsation/sentiment-analysis-api/commit/8dd662b61f36fc59bda8bbbc741db3a0ed77c15f))

- **ci**: Bump docker/login-action from 3 to 4
  ([`ae79aa5`](https://github.com/ntsation/sentiment-analysis-api/commit/ae79aa587735b78770bfef04550b66537059968f))

- **ci**: Bump docker/metadata-action from 5 to 6
  ([`af2881d`](https://github.com/ntsation/sentiment-analysis-api/commit/af2881d10132021ccc014c18dddd0429f2ea8002))

- **ci**: Bump docker/setup-qemu-action from 3 to 4
  ([`75a61f6`](https://github.com/ntsation/sentiment-analysis-api/commit/75a61f624ad3d4e983478a1de60cc26cf10ded5a))

- **ci**: Bump python-semantic-release/python-semantic-release
  ([`8395420`](https://github.com/ntsation/sentiment-analysis-api/commit/8395420b03c45ae69e759dbf199e86adbbf63af6))

- **deps**: Bump locust from 2.46.3 to 2.46.4 in /config
  ([`3477052`](https://github.com/ntsation/sentiment-analysis-api/commit/34770529cb0837d4d7d585c64269eba59c3c6d75))

- **deps**: Bump msgpack from 1.2.1 to 1.2.2 in /config
  ([`980cbe7`](https://github.com/ntsation/sentiment-analysis-api/commit/980cbe7fdec12d5e3041d82a7c0ec1e3c77bccad))

- **deps**: Bump ruff from 0.16.3 to 0.16.4 in /config
  ([`345a47d`](https://github.com/ntsation/sentiment-analysis-api/commit/345a47d55edf6ebd168dc80452b0988f5962d880))

- **deps**: Bump ruff from 0.16.4 to 0.16.5 in /config
  ([`573c7ea`](https://github.com/ntsation/sentiment-analysis-api/commit/573c7ea251d6916b9de2efe4c00e75126a7d2c36))

- **deps**: Bump sentry-sdk from 2.68.0 to 2.68.1 in /config
  ([`6de1782`](https://github.com/ntsation/sentiment-analysis-api/commit/6de17824bdb23c54eebebc36a2ac9cfa1f460ff6))

- **deps**: Update lockfile
  ([`093f0de`](https://github.com/ntsation/sentiment-analysis-api/commit/093f0dee202431fb1a2144533cd582e04a4c95ab))


## v1.3.0 (2026-08-22)

### Chores

- **ci**: Add PR and issue templates
  ([`0cf15d6`](https://github.com/ntsation/sentiment-analysis-api/commit/0cf15d65a18dc968fbaa2b555795dd41e581c55c))

### Features

- **ci**: Notify portfolio to rebuild on push to main
  ([`b9d17e2`](https://github.com/ntsation/sentiment-analysis-api/commit/b9d17e2ea4223f3bc57d34f515973ca2a7b091d9))


## v1.2.1 (2026-08-22)

### Bug Fixes

- **ci**: Ignora vendor do pip no scan trivy
  ([`406bf33`](https://github.com/ntsation/sentiment-analysis-api/commit/406bf3390b4489a4914bc0abdffb9f0dd170595d))


## v1.2.0 (2026-08-22)

### Features

- Ajusta deps
  ([`d4e5b00`](https://github.com/ntsation/sentiment-analysis-api/commit/d4e5b00b5e88b7d285e43531890ca9acc9810152))


## v1.1.0 (2026-08-22)

### Bug Fixes

- Ajusta caminho do pipeline docker
  ([`ffc05f6`](https://github.com/ntsation/sentiment-analysis-api/commit/ffc05f6decf06f1e36cc2e62d282d1412be01714))

- Ajusta pipeline para rodar na main
  ([`71e4f1a`](https://github.com/ntsation/sentiment-analysis-api/commit/71e4f1a0d834a2cb19daa3de7e65c3eef3140752))

- Ajusta readme
  ([`b65ad4e`](https://github.com/ntsation/sentiment-analysis-api/commit/b65ad4efb56c3fd268c0951cf479f6c5a8b6dcab))

- Ajusta ruff
  ([`e2dfe3d`](https://github.com/ntsation/sentiment-analysis-api/commit/e2dfe3da0de9dd06c805611f3fc8dd690ce4102a))

- **ci**: Corrige versao do trivy-action
  ([`593f75f`](https://github.com/ntsation/sentiment-analysis-api/commit/593f75f064d228d0bbdb39f3096235b5cc966a03))

### Chores

- Adiciona testes de carga com locust e requirements de dev
  ([`3f7ead6`](https://github.com/ntsation/sentiment-analysis-api/commit/3f7ead6b39ef20a395843d93868926e4bdca3814))

- Pre-bakeia lexico vader no docker e remove codigo morto
  ([`ec0472d`](https://github.com/ntsation/sentiment-analysis-api/commit/ec0472d5699424c8f73395f6226c36ce2a08f74a))

- **ci**: Bump actions/checkout from 4 to 7
  ([`72ff32f`](https://github.com/ntsation/sentiment-analysis-api/commit/72ff32f0ed84030a71c52556244973461bb340f5))

- **ci**: Bump actions/setup-python from 5 to 7
  ([`a022a0f`](https://github.com/ntsation/sentiment-analysis-api/commit/a022a0fdd03e1d76dad53886181e6c776e889272))

- **ci**: Bump docker/setup-buildx-action from 3 to 4
  ([`964c2dd`](https://github.com/ntsation/sentiment-analysis-api/commit/964c2ddfc7aa16fcec7888ca004bfa5299703eca))

- **deps**: Bump python from 3.12-slim to 3.14-slim in /docker
  ([`a3ea120`](https://github.com/ntsation/sentiment-analysis-api/commit/a3ea120e302264b55b39c40c72c84e040662fe13))

### Continuous Integration

- Adiciona mypy, format check, matrix python e docker build a cada push
  ([`4d3a9dc`](https://github.com/ntsation/sentiment-analysis-api/commit/4d3a9dcea7227f03119a02c8a2e00a5443714dea))

### Documentation

- Adiciona artigo sobre a evolucao da api
  ([`e20654e`](https://github.com/ntsation/sentiment-analysis-api/commit/e20654e78c2a9a2640c44b403ce7c68135eae116))

- Adiciona traducao pt-br do readme e en-us do artigo
  ([`fa29965`](https://github.com/ntsation/sentiment-analysis-api/commit/fa2996508c0f3bd0185277387a17c5f34307ac6d))

- Atualiza readme e adiciona docker compose
  ([`cb2968c`](https://github.com/ntsation/sentiment-analysis-api/commit/cb2968ccd2e7cfd7c4653aae1ed1f5f2518b4a81))

- Documenta versionamento, batch, stream e observabilidade
  ([`cc1b698`](https://github.com/ntsation/sentiment-analysis-api/commit/cc1b698b5757a1789d41ec70d0725c1e60bca915))

### Features

- Add novos pipes
  ([`5c9ac02`](https://github.com/ntsation/sentiment-analysis-api/commit/5c9ac029233e52d562ca86590e1c45073ac58122))

- Adiciona .txt
  ([`83002ae`](https://github.com/ntsation/sentiment-analysis-api/commit/83002aed7940afe3a40ee3df290279193b0dc60c))

- Adiciona arquivo dockerfile
  ([`f39c245`](https://github.com/ntsation/sentiment-analysis-api/commit/f39c245a15c63b6a9a77cef09e1b37c2ba80ed8f))

- Adiciona batch assincrono com job id e stream sse
  ([`5556e7b`](https://github.com/ntsation/sentiment-analysis-api/commit/5556e7bf3aaf4e64c6445cef6f766548aa928240))

- Adiciona benchmark de cache com locust e resultados
  ([`40c3340`](https://github.com/ntsation/sentiment-analysis-api/commit/40c334048c3c0053f581ae6362f889c512be6b54))

- Adiciona estrutura inicial de pastas
  ([`3b2db4e`](https://github.com/ntsation/sentiment-analysis-api/commit/3b2db4ee9aceb7ce7d274d6352b2e4e02a7bb578))

- Adiciona estrutura seguindo o SOLID
  ([`fd6e8d3`](https://github.com/ntsation/sentiment-analysis-api/commit/fd6e8d3bbc693e7429b631ccce17f49355440078))

- Adiciona observabilidade com prometheus, structlog, sentry e workers
  ([`4798572`](https://github.com/ntsation/sentiment-analysis-api/commit/4798572bbf5f3ee7745bddfb3683008903ae1956))

- Adiciona pipeline de formatação
  ([`9de0972`](https://github.com/ntsation/sentiment-analysis-api/commit/9de097238b81afbb1ec96a7249288dc7bec58c59))

- Adiciona pipeline docker
  ([`7cb8936`](https://github.com/ntsation/sentiment-analysis-api/commit/7cb893627a28cca94458f4c71718a1d253848a20))

- Adiciona rate limiting, headers de seguranca, cors e health check
  ([`ecf032f`](https://github.com/ntsation/sentiment-analysis-api/commit/ecf032f19dd3cb4934a7846ede3557e396a39c12))

- Adiciona settings por ambiente e validacao de payload
  ([`42548ad`](https://github.com/ntsation/sentiment-analysis-api/commit/42548ad7bb0f6dc2cac3f3e507e4a377b22fc5e6))

- Adiciona suporte a pt-br com leia, cache de resultados e endpoint admin
  ([`316ef48`](https://github.com/ntsation/sentiment-analysis-api/commit/316ef481826af7e76370c41d25058739ae201af7))

- Adiciona testes unitarios
  ([`d31f5f0`](https://github.com/ntsation/sentiment-analysis-api/commit/d31f5f02071ad17a22f78cf0b00dfb27104361d3))

- Adiciona tratamento de excecoes globais, cobertura de testes e dockerfile otimizado
  ([`0986ffa`](https://github.com/ntsation/sentiment-analysis-api/commit/0986ffa6aea298b281e1ac3f306b4b094334c1f2))

- Adiciona versionamento de api, metadados e openapi rica
  ([`9f99673`](https://github.com/ntsation/sentiment-analysis-api/commit/9f996737ee117bff3d32138bed0b4fc98c0233be))

- Ajussta schedulers
  ([`71006d0`](https://github.com/ntsation/sentiment-analysis-api/commit/71006d067410d7c892f8cad80c440e2d7acf2e30))

- Atualiza gitignore
  ([`cf95161`](https://github.com/ntsation/sentiment-analysis-api/commit/cf9516194543693d56726c6f626aa7421225de9d))

- Troca o black pelo ruff no pipeline CI/CD
  ([`7ac112e`](https://github.com/ntsation/sentiment-analysis-api/commit/7ac112e4528b468cfb823ca502db2f314e575f98))


## v1.0.0 (2024-12-15)

- Initial Release
