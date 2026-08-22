# CHANGELOG

<!-- version list -->

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
