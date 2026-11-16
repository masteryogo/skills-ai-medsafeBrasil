# Segredos, supply chain, infraestrutura e resposta a incidente

Referência de apoio da skill `security-engineer`.

## 1. Segredos

- **Inventário primeiro**: liste toda credencial em uso (banco, API externa, provedor de
  modelo, storage, fila, certificado, chave de assinatura), com dono, escopo e onde vive.
  Não dá para proteger o que ninguém listou.
- Origem única: cofre (Vault, Secrets Manager, KMS, Key Vault) ou injeção em runtime pelo
  orquestrador. Arquivo `.env` local fica no `.gitignore` e nunca no repositório.
- Escopo mínimo e credencial **por serviço**, nunca compartilhada entre times — credencial
  compartilhada não pode ser rotacionada sem coordenação, então nunca é rotacionada.
- Rotação: procedimento escrito e **testado** antes de precisar. Prefira credencial de vida
  curta emitida por identidade (OIDC no CI, IAM role, workload identity) a chave estática.
- Vazou: revogue primeiro, investigue depois. Remover o commit não basta — o segredo já foi
  clonado, indexado e possivelmente usado. Verifique log de uso da credencial.
- Varredura de segredo no pre-commit e no CI, mais uma varredura do histórico completo.

## 2. Dependências e supply chain

- Lockfile comitado, instalação com `--frozen-lockfile`/`ci`, build reprodutível.
- Fixe por versão exata; em imagem de container, por digest.
- **Triagem** de alerta: o pacote é usado? o caminho vulnerável é alcançável a partir de
  entrada externa? é dependência de desenvolvimento? Corrigir por ordem de exploitabilidade,
  e registrar o que foi aceito e por quê.
- Ataques a observar ao adicionar dependência nova: nome parecido com pacote popular
  (typosquatting), pacote novo com poucos downloads, script de pós-instalação, mantenedor
  recém-trocado, e dependência interna resolvida do registro público (confusão de nome).
- SBOM (CycloneDX ou SPDX) gerado no build e guardado com o artefato: é o que permite
  responder "somos afetados?" em horas em vez de dias.
- Assine artefato e verifique na implantação quando o ambiente permitir.

## 3. CI/CD

- Segredo por job, com escopo mínimo; nada de segredo disponível em workflow disparado por
  fork.
- Não execute código de PR não confiável em runner com credencial — separe o job que
  constrói do job que publica.
- Fixe ações e imagens por commit/digest, não por tag móvel.
- Proteja o branch principal: revisão obrigatória, sem push forçado, sem pular verificação.
- Runner auto-hospedado é máquina de execução de código arbitrário: efêmero, isolado, sem
  credencial de nuvem ampla.
- Registre quem publicou o quê e quando; a esteira é parte da cadeia de custódia.

## 4. Infraestrutura e nuvem

- IAM sem `*` em ação ou recurso; papel por serviço; sem chave de usuário permanente quando
  houver identidade federada.
- Storage privado por padrão, criptografia em repouso, versionamento e bloqueio de exclusão
  em bucket que guarda dado crítico.
- Rede: exposição mínima, segmentação entre camadas, banco sem IP público, egress restrito
  (é o que trava exfiltração).
- Container: base mínima fixada por digest, usuário não-root, sem segredo em camada,
  filesystem só-leitura, limites de CPU e memória, sem `--privileged`.
- Log de auditoria (CloudTrail e equivalentes) habilitado em todas as regiões, com retenção
  definida e proteção contra apagamento pelo próprio invasor.
- Backup: testado com restauração real, cópia isolada da conta principal, retenção compatível
  com a janela de detecção — backup que o atacante consegue apagar não é backup.

## 5. Detecção — os poucos alertas que valem

Um alerta que ninguém investiga é pior que nenhum. Comece por estes:

- login com sucesso após muitas falhas; login de local ou horário atípico para a conta;
- uso de credencial de serviço a partir de origem nova;
- criação de usuário, chave de acesso ou permissão administrativa;
- desativação de log de auditoria ou de alerta;
- volume anômalo de leitura/exportação em base com dado pessoal;
- egress para domínio não visto antes a partir de servidor de produção;
- em aplicação com LLM: pico de custo, pico de chamadas de ferramenta por sessão, ou
  chamadas para destino fora da allowlist.

Cada alerta precisa de dono, procedimento de triagem e critério de encerramento.

## 6. Resposta a incidente

### Antes (o que decide o resultado)

Contato e escalonamento definidos, acesso de emergência testado, canal de comunicação
alternativo (se o comprometido for o corporativo), procedimento de rotação pronto, e
retenção de log suficiente para reconstruir semanas — não horas.

### Durante

1. **Preservar** — antes de reinstalar ou reiniciar: imagem de disco, cópia de log, memória
   quando viável, e registro do horário de cada ação (linha do tempo começa agora).
2. **Conter** — isolar host da rede sem desligar (perde memória), revogar sessão e token,
   rotacionar credencial exposta, bloquear a conta usada. Assuma que tudo legível pelo
   processo comprometido vazou.
3. **Escopo** — o que foi acessado, por quanto tempo, a partir de onde, com qual credencial;
   procurar persistência (chave de acesso nova, tarefa agendada, webhook, regra de
   encaminhamento de e-mail, colaborador adicionado no repositório).
4. **Erradicar** — corrigir a causa; recuperar de fonte confiável, nunca do sistema afetado.
5. **Recuperar** — restaurar serviço com monitoramento reforçado por um período definido.
6. **Comunicar** — jurídico, DPO e clientes conforme obrigação legal. Em dado pessoal,
   verifique o dever de notificação à ANPD e aos titulares e o prazo em vigor na
   regulamentação atual antes de afirmar um número.
7. **Aprender** — post-mortem sem culpado, com ações que mudam o desenho (o que faltou
   limitar, o que faltou detectar), cada uma com dono e prazo.

### O que não fazer

Reinstalar antes de coletar evidência; comunicar antes de conhecer o escopo; declarar fim sem
buscar persistência; trocar a senha e considerar resolvido; discutir o incidente no canal que
pode estar comprometido.

## 7. Formato de achado (para relatório)

Um achado útil tem, sempre:

- **Título** direto: o que é possível fazer, por quem.
- **Impacto** no negócio, não a categoria genérica.
- **Pré-requisitos** do atacante (anônimo? autenticado? em que papel?).
- **Reprodução** mínima, passo a passo, sem dado pessoal real no texto.
- **Correção recomendada**, com a alternativa de mitigação temporária quando a definitiva for
  cara.
- **Severidade** justificada por impacto × facilidade, com o raciocínio visível.

Ordene o relatório por risco, e coloque no topo o que dá para corrigir esta semana.
