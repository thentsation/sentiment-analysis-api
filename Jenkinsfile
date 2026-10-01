// Pipeline da plataforma (Shared Library "platform", repo devops-platform/jenkins-lib).
// PRs e branches: validação, CI (docker build --target test), pip-audit e Trivy.
// main: build, smoke test, push, deploy atrás do Traefik com rollback, release
// (semantic-release), rebuild do portfolio e rebuild semanal.
@Library('platform') _

appPipeline(
    name: 'sentiment-analysis-api',
    host: 'sentiment.137-131-175-7.sslip.io',
    healthPath: '/health',
    // O /health devolve só {"status":"ok"}, sem versão.
    healthExpectsVersion: false,
    deployBranch: 'main',
    // GHSA-8mgp-746c-j5xp: path-sandbox bypass nas APIs de modelo do nltk
    // (TransitionParser, AveragedPerceptron, PerceptronTagger), que o app não usa
    // (só download()/data.find()/vader); ainda sem correção publicada.
    pipAuditIgnore: ['GHSA-8mgp-746c-j5xp'],
    notify: [[repo: 'ntsation/portfolio', event: 'rebuild']],
)
