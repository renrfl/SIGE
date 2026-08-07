# SIGE - Documento de Arquitetura e Continuidade do Projeto

## Objetivo

O SIGE é um Sistema de Gestão de Endereçamento. Seu objetivo é controlar
o endereço físico dos produtos dentro do depósito. Não é um WMS e não
faz controle de estoque.

## Hierarquia oficial

Rua → Prédio → Módulo → Nível → Posição

Definições: - Rua = corredor do depósito. - Prédio = conjunto de
porta-paletes. - Módulo = vão do porta-palete. - Nível = altura. -
Posição = divisão horizontal do módulo.

## Regras obrigatórias do desenvolvimento

-   Um arquivo por resposta.
-   Sempre enviar o arquivo completo.
-   Nunca enviar apenas trechos.
-   Preservar compatibilidade.
-   Evitar mudanças desnecessárias.
-   Explicações curtas; detalhar apenas quando realmente importante.
-   Responder preferencialmente em: Arquivo / Código / Teste.
-   Sugerir commit antes de alterações grandes.

## Filosofia

Priorizar estabilidade e simplicidade. O código deve refletir a operação
logística real.

## Estado atual

-   Busca inteligente de produtos.
-   Dashboard administrativo.
-   Importação CSV.
-   Impressão de etiquetas.
-   Produto inativo não aparece em novos endereçamentos.
-   Confirmação para substituir posição ocupada.
-   Rua, Prédio, Módulo e Nível usam inativação.
-   Posição só pode ser excluída quando vazia.

## Perfis futuros

Administrador: tudo. Operador: cadastrar, editar, inativar e imprimir.
Usuário: somente consulta.

## Roadmap

### v1.1

-   Backup e restauração SQLite.
-   Busca inteligente de posições.
-   Tratamento de estruturas inativas.
-   Produto inativo já endereçado.
-   Movimentação segura de endereço.

### v1.2

-   Assistente de criação em massa.
-   Padronização automática dos códigos.
-   Melhorias mobile.
-   Recursos totalmente locais (Bootstrap/JS).
-   Perfis de acesso.

### Futuro

-   Histórico de movimentações.
-   Auditoria.
-   Múltiplos endereços.
-   Melhorias de concorrência.

## Convenções

-   Flask + SQLAlchemy + SQLite.
-   GitHub e ZIP mais recente são a fonte oficial.
-   Antes de implementar, avaliar impacto operacional.

## Prompt de continuidade

Considere o ZIP anexado como a fonte oficial do projeto. Nunca responda
com trechos de código. Sempre envie arquivos completos. Preserve a
arquitetura existente. Priorize estabilidade para produção. Explique
somente quando necessário. Sugira commit antes de mudanças
significativas. O objetivo do SIGE é exclusivamente o endereçamento
logístico.
